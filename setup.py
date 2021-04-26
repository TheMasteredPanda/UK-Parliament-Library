import setuptools

setuptools.setup(
            name="ukparliament",
            version="2.4.11",
            author="TheMasteredPanda",
            description="A Python Library used to fetch member, bills, and voting data from the UK Parliament Rest API",
            url="https://github.com/TheMasteredPanda/UK-Parliament-Library",
            project_urls={
                "Bug Tracker": "https://github.com/TheMasteredPanda/UK-Parliament-Library/issues"
                },

            package_dir={"": "src"},
            packages=setuptools.find_packages(where="src"),
            python_requires=">=3.9"
        )
