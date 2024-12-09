from setuptools import setup

setup(
    name='pysyun_timeline_anomaly_detector',
    version='1.0.0',
    author='Illia Tsokolenko',
    author_email='illiatea2@gmail.com',
    py_modules=['pysyun.anomaly.detector', 'pysyun.anomaly.extractor'],
    install_requires=['pandas', 'numpy', 'scipy'],
    url='https://github.com/pysyun/pysyun_timeline_anomaly_detector'
)