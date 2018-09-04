from setuptools import setup, find_packages

setup(name='tacle',
      version='0.6.9',
      description='TaCLe is a tool for learning constraints and formulas',
      url='http://github.com/samuelkolb/tacle.git',
      author='Samuel Kolb',
      author_email='samuel.kolb@me.com',
      license='MIT',
      packages=find_packages(),
      zip_safe=False, install_requires=['numpy', 'python-constraint', 'matplotlib'],
      setup_requires=['pytest-runner'],
      tests_require=["pytest"]
)