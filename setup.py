from setuptools import setup

setup(name='tacle',
      version='0.2',
      description='TaCLe is a tool for learning constraints and formulas',
      url='http://github.com/samuelkolb/tacle.git',
      author='Samuel Kolb',
      author_email='samuel.kolb@me.com',
      license='MIT',
      packages=['tacle'],
      zip_safe=False, install_requires=['numpy', 'python-constraint', 'matplotlib']
      )