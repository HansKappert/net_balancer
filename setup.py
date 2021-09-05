from setuptools import setup

setup(
    name='net_balancer',
    packages=['net_balancer','service'],
    include_package_data=True,
    install_requires=[
        'flask',
    ],
)