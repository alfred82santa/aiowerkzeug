from setuptools import setup
import os

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as desc_file:
    description = desc_file.read().replace(':class:', '').replace(':func:', '')

setup(
    name='aiowerkzeug',
    url='https://github.com/alfred82santa/aiowerkzeug',
    author='alfred82santa',
    version='0.2.0',
    author_email='alfred82santa@gmail.com',
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha'],
    packages=['aiowerkzeug'],
    include_package_data=True,
    install_requires=['werkzeug', 'hachiko', 'aiohttp'],
    description="Werkzeug for asyncio",
    long_description=description,
    test_suite="nose.collector",
    tests_require="nose",
    zip_safe=True,
)
