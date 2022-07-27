import setuptools

setuptools.setup(
    name="quicksight_lambda",
    version="0.0.1",
    description="Lambda function that registers Quicksight users",
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    author="Eric Riddoch",
    package_dir={"": "."},
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=["python-jose"],
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
