Preflib-Django
==============

This repository contains the Django project for the `PrefLib.org website <https://www.preflib.org/>`_. It is meant to be used by people who know how Django works. If it is not your case and you want to learn more about Django, check the `Django project page <https://www.djangoproject.com/>`_ that has some quite nice tutorials.

Setting Up the Website
======================

If you want to play around with the website, after cloning the repository, run the quick-setup script:

.. code-block:: bash

	python3 quicksetup.py

This script creates all the required folders and files. Note that you might need to install additional python packages for the script to run through. After the script is done, we advice to add some data to the newly created website. To do so, first download some zipped datasets from `PrefLib.org website <https://www.preflib.org/>`_. You can use the following links:

* **AGH course selection**: `https://www.preflib.org/static/data/ED/agh/agh.zip <https://www.preflib.org/static/data/ED/agh/agh.zip>`_
* **Aspen election data**: `https://www.preflib.org/static/data/ED/aspen/aspen.zip <https://www.preflib.org/static/data/ED/aspen/aspen.zip>`_

The zip files should be place in :code:`preflibApp/static/datatoadd`. Once you have put all the zip files in the folder, run the following command:

.. code-block:: bash

	python3 manage.py adddataset --all

You are now almost done, just run two more scripts all you will have a fully functional website.

.. code-block:: bash

	python3 manage.py updatemetadata
	python3 manage.py generatezip

Note that these two last scripts can take long, especially if you have added a lot of data.