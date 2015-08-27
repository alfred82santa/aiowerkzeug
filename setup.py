from setuptools import setup
import os

setup(
    name='aiowerkzeug',
    url='https://github.com/alfred82santa/aiowerkzeug',
    author='alfred82santa',
    version='0.1.0',
    author_email='alfred82santa@gmail.com',
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.4',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha'],
    packages=['aiowerkzeug'],
    include_package_data=True,
    install_requires=['werkzeug'],
    description="Werkzeug for asyncio",
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    test_suite="nose.collector",
    tests_require="nose",
    zip_safe=True,
)
