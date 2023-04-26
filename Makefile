TMP ?= /tmp
current_dir = $(shell pwd)

.PHONY: _pip_pkg pip_pkg _pip_pkg_push pip_pkg_push _deb \
	deb docker_run docker_build docker_push _build_doc build_doc \
	doc_test_debian _doc_test_debian doc_test_pip _doc_test_pip \
	pip_pkg_check _pip_pkg_check _pip_functional_tests _pip_pkg_functional_tests _deb_pkg_functional_tests \
    _common_pip_functional_tests _rf_functional_tests functional_tests

# Empty default target, since the debian packagin runs `make`
all:
	@echo

_pip_pkg:
	virtualenv /venv
	/venv/bin/pip install build
	/venv/bin/python3 -m build .

pip_pkg:
	mkdir -p dist
	docker run --rm -v $(current_dir):/sosse-ro:ro -v $(current_dir)/dist:/sosse/dist biolds/sosse:pip-base bash -c 'cd /sosse && tar -C /sosse-ro --exclude=.git -caf - . | tar xf - && make _pip_pkg'

_pip_pkg_push:
	virtualenv /venv
	/venv/bin/pip install twine
	@echo ==============================================================================================
	@echo 'Uploading to Pypi, please use "__token__" as username, and the token (pypi-xxxxxx) as password'
	@echo ==============================================================================================
	/venv/bin/twine upload --verbose dist/*

pip_pkg_push:
	docker run --rm -v $(current_dir):/sosse:ro -ti biolds/sosse:pip-base bash -c 'cd /sosse && make _pip_pkg_push'

_deb:
	dpkg-buildpackage -us -uc
	mv ../sosse*_amd64.deb /deb/

deb:
	mkdir $(current_dir)/deb/ &>/dev/null ||:
	docker run --rm -v $(current_dir):/sosse:ro -v $(current_dir)/deb:/deb biolds/sosse:debian-pkg bash -c 'cp -x -r /sosse /sosse-deb && make -C /sosse-deb _deb'

_build_doc:
	. /opt/sosse-doc/bin/activate ; make -C doc linkcheck html SPHINXOPTS="-W"

build_doc:
	mkdir -p doc/build/
	docker run --rm -v $(current_dir):/sosse:ro -v $(current_dir)/doc/build:/sosse/doc/build biolds/sosse:doc bash -c 'cd /sosse && make _build_doc'


docker_run:
	docker volume inspect sosse_postgres &>/dev/null || docker volume create sosse_postgres
	docker volume inspect sosse_var &>/dev/null || docker volume create sosse_var
	docker run -p 8005:80 --mount source=sosse_postgres,destination=/var/lib/postgresql \
						--mount source=sosse_var,destination=/var/lib/sosse biolds/sosse:latest

docker_push:
	$(MAKE) -C docker push
	docker push biolds/sosse:latest

docker_build:
	$(MAKE) -C docker build
	docker build --build-arg APT_PROXY=$(APT_PROXY) --build-arg PIP_INDEX_URL=$(PIP_INDEX_URL) --build-arg PIP_TRUSTED_HOST=$(PIP_TRUSTED_HOST) -t biolds/sosse:latest .

_doc_test_debian:
	cp doc/code_blocks.json /tmp/code_blocks.json
	grep -q 'apt install -y python3-django/bullseye-backports sosse' /tmp/code_blocks.json
	sed -e 's#apt install -y python3-django/bullseye-backports sosse#apt install -y python3-django/bullseye-backports sosse; /etc/init.d/nginx start \& /etc/init.d/postgresql start \& bash ./tests/wait_for_pg.sh#' -i /tmp/code_blocks.json
	bash ./tests/doc_test.sh /tmp/code_blocks.json install/debian

doc_test_debian:
	docker run -v $(current_dir):/sosse:ro debian:bullseye bash -c 'cd /sosse && apt-get update && apt-get install -y make jq && make _doc_test_debian'

_doc_test_pip:
	apt install -y chromium chromium-driver postgresql nginx python3-dev libpq-dev
	/etc/init.d/postgresql start &
	bash ./tests/wait_for_pg.sh
	bash ./tests/doc_test.sh doc/code_blocks.json install/pip

doc_test_pip:
	docker run -v $(current_dir):/sosse:ro debian:bullseye bash -c 'cd /sosse && apt-get update && apt-get install -y make jq && make _doc_test_pip'

_pip_pkg_check:
	pip install twine
	twine check dist/*

pip_pkg_check:
	docker run --rm -v $(current_dir):/sosse:ro biolds/sosse:pip-base bash -c 'cd /sosse && make _pip_pkg_check'

_pip_functional_tests:
	make _common_pip_functional_tests
	/etc/init.d/postgresql start &
	bash ./tests/wait_for_pg.sh
	grep -q 'pip install sosse' /tmp/code_blocks.json
	sed -e 's#pip install sosse#pip install ./#' -i /tmp/code_blocks.json
	bash ./tests/doc_test.sh /tmp/code_blocks.json install/pip

_pip_pkg_functional_tests:
	make _common_pip_functional_tests
	/etc/init.d/postgresql start &
	bash ./tests/wait_for_pg.sh
	grep -q 'pip install sosse' /tmp/code_blocks.json
	sed -e 's#pip install sosse#pip install dist/*.whl#' -i /tmp/code_blocks.json
	bash ./tests/doc_test.sh /tmp/code_blocks.json install/pip

_common_pip_functional_tests:
	cp doc/code_blocks.json /tmp/code_blocks.json
	grep -q 'sosse-admin default_conf' /tmp/code_blocks.json
	sed -e 's#sosse-admin default_conf#sosse-admin default_conf | sed -e \\"s/^.browser_options=.*/browser_options=--enable-precise-memory-info --disable-default-apps --incognito --headless --no-sandbox/\\"#' -e 's/^.debug=.*/debug=true/' -i /tmp/code_blocks.json # add --no-sandbox to chromium's command line

_deb_pkg_functional_tests:
	echo 'deb http://deb.debian.org/debian bullseye-backports main' > /etc/apt/sources.list.d/bullseye-backports.list
	apt update
	grep ^Depends: debian/control | sed -e "s/.*},//" -e "s#python3-django [^,]*,#python3-django/bullseye-backports#g" -e "s/,//g" | xargs apt install -y
	grep '^ExecStartPre=' debian/sosse-uwsgi.service | sed -e 's/^ExecStartPre=-\?+\?//' -e 's/^/---- /'
	bash -c "`grep '^ExecStartPre=' debian/sosse-uwsgi.service | sed -e 's/^ExecStartPre=-\?+\?//'`"
	cp doc/code_blocks.json /tmp/code_blocks.json
	grep -q 'apt install -y python3-django/bullseye-backports sosse' /tmp/code_blocks.json
	sed -e 's#apt install -y python3-django/bullseye-backports sosse#apt install -y python3-django/bullseye-backports sudo; dpkg -i deb/*.deb ; /etc/init.d/postgresql start \& bash ./tests/wait_for_pg.sh#' -i /tmp/code_blocks.json
	bash ./tests/doc_test.sh /tmp/code_blocks.json install/debian
	sed -e 's/^.browser_options=.*/browser_options=--enable-precise-memory-info --disable-default-apps --incognito --headless --no-sandbox/' -e 's/^.debug=.*/debug=true/' -i /etc/sosse/sosse.conf # add --no-sandbox to chromium's command line
	/etc/init.d/nginx start
	bash -c 'uwsgi --uid www-data --gid www-data --plugin python3 --ini /etc/sosse/uwsgi.ini --logto /var/log/sosse/uwsgi.log & sudo -u www-data sosse-admin crawl &'
	bash ./tests/docker_run.sh docker/pip-test/Dockerfile

_rf_functional_tests:
	virtualenv /rf-venv
	/rf-venv/bin/pip install -r tests/robotframework/requirements.txt
	cd ./tests/robotframework && /rf-venv/bin/robot --exitonerror --exitonfailure *_*.robot

functional_tests:
	docker run --rm -v $(current_dir):/sosse biolds/sosse:pip-test bash -c 'cd /sosse && make _pip_functional_tests _rf_functional_tests'
