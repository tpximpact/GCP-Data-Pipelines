from setuptools import setup

setup(
    name="data-pipeline-tools",
    version="1.0",
    packages=["data_pipeline_tools"],
    url="https://github.com/tpximpact/GCP-Data-Pipelines.git",
    install_requires=["pandas", "aiohttp", "google-cloud"],
)
