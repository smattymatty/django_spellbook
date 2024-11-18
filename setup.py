from setuptools import setup, find_packages

setup(
    name='django-spellbook',
    version='0.0.4',  # Increment version
    author='Mathew Storm',
    author_email='mathewstormdev@gmail.com',
    description='A Django library for creating and managing content blocks in markdown for developers and bloggers',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/django-spellbook',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'django_spellbook': [
            'templates/*.html',
            'templates/*/*.html',
            'templates/*/*/*.html',
            'static/*',
            'static/*/*',
        ],
    },
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
        'Intended Audience :: Other Audience',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    python_requires='>=3.10',
    project_urls={
        'Bug Reports': 'https://github.com/smattymatty/django_spellbook/issues',
        'Source': 'https://github.com/smattymatty/django_spellbook',
    },
)
