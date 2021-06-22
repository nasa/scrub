
mkdir classes
javac -verbose -d ./classes -classpath ./classes:./../lib/servlet-api.jar:./../lib/commons-lang-2.5.jar:./../lib/commons-codec-1.5.jar:./../lib/javamail-1.4.4.jar -sourcepath ./ -g -Xlint:all ./testcasesupport/*.java
javac -verbose -d ./classes -classpath ./classes:./../lib/servlet-api.jar:./../lib/commons-lang-2.5.jar:./../lib/commons-codec-1.5.jar:./../lib/javamail-1.4.4.jar -sourcepath ./ -g -Xlint:all ./testcases/CWE835_Infinite_Loop/*.java
