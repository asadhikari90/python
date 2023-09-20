setup(
    # ...
    entry_points={
        'console_scripts': [
            'test-with-coverage = main.py.tests.run_tests_with_coverage:main',
        ],
    },
)
