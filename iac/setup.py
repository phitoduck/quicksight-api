import setuptools

setuptools.setup(
    name="quicksight_iac",
    version="0.0.1",
    description="An empty CDK Python app",
    # long_description=long_description,
    long_description_content_type="text/markdown",
    author="Eric Riddoch",
    package_dir={"": "."},
    packages=setuptools.find_packages(),
    install_requires=[
        "aws-cdk-lib==2.27.0",
        "constructs>=10.0.0,<11.0.0",
        "aws-cdk.aws-apigatewayv2-alpha==2.27.0a0",
        "aws-cdk.aws-apigatewayv2-integrations-alpha==2.27.0a0",
        "aws-cdk.aws_apigatewayv2_authorizers_alpha==2.27.0a0",
        "aws-cdk.aws_glue_alpha==2.27.0a0",
    ],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
