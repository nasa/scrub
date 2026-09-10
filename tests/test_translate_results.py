import json
import pathlib

import pytest

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


@pytest.mark.parametrize('line', [0, None, -1, 12])
@pytest.mark.parametrize('with_flow', [False, True])
def test_sarif_output_omits_unknown_line_regions(tmp_path, line, with_flow):
    """Unknown lines retain their file location without an invalid startLine."""
    output_file = tmp_path / 'results.sarif'
    flow = [translate_results.create_code_flow(tmp_path / 'trace.c', line, 'Trace step')] if with_flow else []
    warning = translate_results.create_warning(
        'tool001', tmp_path / 'source.c', line, ['File finding'], 'tool',
        query='R1', code_flow=flow
    )
    translate_results.create_sarif_output_file([warning], '2.1.0', output_file, tmp_path, 'tool')
    output = json.loads(output_file.read_text())
    assert_valid_sarif_2_1(output)
    result = output['runs'][0]['results'][0]
    locations = [result['locations'][0]['physicalLocation']]
    if with_flow:
        locations.append(result['codeFlows'][0]['threadFlows'][0]['locations'][0]['location']['physicalLocation'])
    for location in locations:
        assert location['artifactLocation']['uri']
        if line == 12:
            assert location['region'] == {'startLine': 12}
        else:
            assert 'region' not in location


@pytest.mark.parametrize('with_flow', [False, True])
def test_sarif_file_level_locations_round_trip(tmp_path, with_flow):
    """Valid SARIF without source regions stays valid through the public translator."""
    input_file = tmp_path / 'input.sarif'
    output_file = tmp_path / 'output.sarif'
    result = {
        'ruleId': 'R1',
        'message': {'text': 'File finding'},
        'locations': [{'physicalLocation': {'artifactLocation': {'uri': 'source.c'}}}],
    }
    if with_flow:
        result['codeFlows'] = [{'threadFlows': [{'locations': [{
            'location': {
                'message': {'text': 'Trace step'},
                'physicalLocation': {'artifactLocation': {'uri': 'trace.c'}},
            }
        }]}]}]
    source = {
        'version': '2.1.0',
        'runs': [{'tool': {'driver': {'name': 'tool'}}, 'results': [result]}],
    }
    assert_valid_sarif_2_1(source)
    input_file.write_text(json.dumps(source))
    assert translate_results.perform_translation(input_file, output_file, tmp_path, 'sarifv2.1.0') == 0
    output = json.loads(output_file.read_text())
    assert_valid_sarif_2_1(output)
    output_result = output['runs'][0]['results'][0]
    assert output_result['ruleId'] == 'R1'
    assert output_result['message']['text'] == 'File finding'
    assert len(output['runs'][0]['results']) == 1
    assert 'region' not in output_result['locations'][0]['physicalLocation']
    if with_flow:
        step = output_result['codeFlows'][0]['threadFlows'][0]['locations'][0]['location']
        assert step['message']['text'] == 'Trace step'
        assert step['physicalLocation']['artifactLocation']['uri'].endswith('trace.c')
        assert 'region' not in step['physicalLocation']
