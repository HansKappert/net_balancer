from setuptools import setup

setup(
    name='net_balancer',
    version='0.1.0',
    author='Hans Kappert',
    author_email='hans.kappert@gmaill.com',
   
    packages=['net_balancer','service'],
    include_package_data=True,
    description='A program that sends purplus power to your Teslq',
    long_description=open('README.md').read(),  
    install_requires=[
        'flask',
    ],
)
