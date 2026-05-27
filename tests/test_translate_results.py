import json
import pathlib

from jsonschema import Draft7Validator

from scrub.tools.parsers import translate_results

SARIF_2_1_SCHEMA = json.loads(
    pathlib.Path(__file__).parent.joinpath('schemas/sarif-2.1.0.json').read_text()
)
SARIF_2_1_VALIDATOR = Draft7Validator(SARIF_2_1_SCHEMA)


def assert_valid_sarif_2_1(sarif_output):
    errors = sorted(SARIF_2_1_VALIDATOR.iter_errors(sarif_output), key=lambda error: error.path)
    assert errors == []


def test_create_sarif_output_schema_url_uses_requested_version(tmp_path):
    output_file = tmp_path.joinpath('results.sarif')

    translate_results.create_sarif_output_file([], '2.0.0', output_file, tmp_path, 'test-tool')

    sarif_output = json.loads(output_file.read_text())

    assert sarif_output['$schema'] == 'https://json.schemastore.org/sarif-2.0.0.json'


def test_create_sarif_2_1_output_uses_driver_rules_for_empty_results(tmp_path):
    output_file = tmp_path.joinpath('empty.sarif')

    translate_results.create_sarif_output_file([], '2.1.0', output_file, tmp_path, 'test-tool')

    sarif_output = json.loads(output_file.read_text())
    tool = sarif_output['runs'][0]['tool']

    assert sarif_output['$schema'] == 'https://json.schemastore.org/sarif-2.1.0.json'
    assert 'rules' not in tool
    assert tool['driver']['rules'] == []
    assert sarif_output['runs'][0]['results'] == []
    assert_valid_sarif_2_1(sarif_output)


def test_create_sarif_2_1_output_uses_driver_rules_and_preserves_results(tmp_path):
    source_root = tmp_path.joinpath('source')
    warning_file = source_root.joinpath('example.c')
    output_file = tmp_path.joinpath('results.sarif')
    results = [
        translate_results.create_warning(
            'tool1',
            warning_file,
            12,
            ['first warning'],
            'test-tool',
            query='RULE001'
        )
    ]

    translate_results.create_sarif_output_file(results, '2.1.0', output_file, source_root, 'test-tool')

    sarif_output = json.loads(output_file.read_text())
    run = sarif_output['runs'][0]
    tool = run['tool']

    assert 'rules' not in tool
    assert tool['driver']['rules'] == [
        {
            'id': 'RULE001',
            'shortDescription': {
                'text': 'RULE001'
            }
        }
    ]
    assert len(run['results']) == 1
    assert run['results'][0]['ruleId'] == 'RULE001'
    assert run['results'][0]['message']['text'] == 'first warning'
    assert run['results'][0]['locations'][0]['physicalLocation']['region']['startLine'] == 12
    assert_valid_sarif_2_1(sarif_output)
