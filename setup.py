from setuptools import setup

setup(
    name='house_notifier',
    packages=['house_notifier'],
    include_package_data=True,
    install_requires=[
        'flask',
        'pyfcm',
    ],
    setup_requires=[
    ],
    tests_require=[
    ],
)