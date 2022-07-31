#!/bin/bash

LOCAL_JAR_FILES_DIR="./volumes/maven_jars/"
mkdir -p "$LOCAL_JAR_FILES_DIR"
wget https://repo1.maven.org/maven2/com/springml/spark-salesforce_2.11/1.1.1/spark-salesforce_2.11-1.1.1.jar -o "$LOCAL_JAR_FILES_DIR"
wget https://repo1.maven.org/maven2/com/springml/salesforce-wave-api/1.0.9/salesforce-wave-api-1.0.9.jar -o "$LOCAL_JAR_FILES_DIR"
wget https://repo1.maven.org/maven2/com/force/api/force-partner-api/40.0.0/force-partner-api-40.0.0.jar -o "$LOCAL_JAR_FILES_DIR"
wget https://repo1.maven.org/maven2/com/force/api/force-wsc/40.0.0/force-wsc-40.0.0.jar -o "$LOCAL_JAR_FILES_DIR"

wget https://repo1.maven.org/maven2/com/fasterxml/jackson/dataformat/jackson-dataformat-xml/2.10.3/jackson-dataformat-xml-2.10.3.jar
wget https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-core/2.10.3/jackson-core-2.10.3.jar