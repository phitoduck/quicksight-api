from pathlib import Path
import requests

THIS_DIR = Path(__file__).parent
MAVEN_JARS_DIR = THIS_DIR / "volumes/maven_jars"

SALESFORCE_MAVEN_JARS = [
    "force-partner-api-40.0.0.jar",
    "force-wsc-40.0.0.jar",
    "salesforce-wave-api-1.0.9.jar",
    "spark-salesforce_2.11-1.1.1.jar",
]

SALESFORCE_MAVEN_URLS = [
    "https://repo1.maven.org/maven2/com/force/api/force-partner-api/40.0.0/force-partner-api-40.0.0.jar",
    "https://repo1.maven.org/maven2/com/force/api/force-wsc/40.0.0/force-wsc-40.0.0.jar",
    "https://repo1.maven.org/maven2/com/springml/salesforce-wave-api/1.0.9/salesforce-wave-api-1.0.9.jar",
    "https://repo1.maven.org/maven2/com/springml/spark-salesforce_2.11/1.1.1/spark-salesforce_2.11-1.1.1.jar",
    # https://stackoverflow.com/questions/67063848/springml-salesforce-cannot-create-xmlstreamreader-from-org-codehaus-stax2-io-st
    "https://repo1.maven.org/maven2/org/codehaus/woodstox/woodstox-core-asl/4.4.1/woodstox-core-asl-4.4.1.jar",
]


def download_file(url: str, local_fpath: Path):
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_fpath, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)
    return local_fpath


def download_maven_jar(url: str):
    fname = url.strip().split("/")[-1]
    fpath = MAVEN_JARS_DIR / fname
    download_file(url=url, local_fpath=fpath)


if __name__ == "__main__":
    for url in SALESFORCE_MAVEN_URLS:
        download_maven_jar(url=url)
