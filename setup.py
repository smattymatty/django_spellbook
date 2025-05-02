from setuptools import setup, find_namespace_packages

setup(
    name='django-spellbook',
    version='0.1.13b2',  # Increment version
    author='Mathew Storm',
    author_email='mathewstormdev@gmail.com',
    description='A Django library for creating and managing content blocks in markdown for developers and bloggers',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/smattymatty/django_spellbook',
    packages=find_namespace_packages(include=['django_spellbook', 'django_spellbook.*']),
    include_package_data=True,
    license='MIT', 
    install_requires=[
        'django>=5.0',
        'markdown>=3.0',
        'pyyaml>=6.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Framework :: Django :: 5.0',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.10',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.10',
    project_urls={
        'Documentation': 'https://django-spellbook.org/',
        'Bug Reports': 'https://github.com/smattymatty/django_spellbook/issues',
        'Source': 'https://github.com/smattymatty/django_spellbook',
    },
)
