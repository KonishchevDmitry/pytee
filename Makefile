.PHONY: all clean distclean install uninstall
.PHONY: install-desktop install-icons
.PHONY: uninstall-desktop uninstall-icons

PREFIX := /usr
bindir := $(PREFIX)/bin
datarootdir := $(PREFIX)/share

system := $(shell uname -s)
program_unix_name := pytee
data_dir := $(datarootdir)/$(program_unix_name)


all:

ifeq ($(system),Darwin)
else
install: install-desktop install-icons
install: uninstall-desktop uninstall-icons
endif


install: all
	set -e; for file in mplayer/*.py $$(find pycl pysd pytee subtitles -name '*.py'; find icons -name '*.png' -o -name '*.svg'); do \
		install -d $(DESTDIR)$(data_dir)/$$(dirname $$file); \
		install -m 0644 $$file $(DESTDIR)$(data_dir)/$$file; \
	done
	install -d $(DESTDIR)$(bindir)
	echo '#!/bin/sh\nexec $(data_dir)/$(program_unix_name)/main.py "$$@"' > $(DESTDIR)$(bindir)/$(program_unix_name)
	chmod a+x $(DESTDIR)$(data_dir)/$(program_unix_name)/main.py
	chmod a+x $(DESTDIR)$(bindir)/$(program_unix_name)

install-desktop:
	set -e; for file in $$(find icons -name '*.png' -o -name '*.svg'); do \
		install -d $(DESTDIR)$(datarootdir)/icons/hicolor/$$(dirname $${file#*/}); \
		install -m 0644 $$file $(DESTDIR)$(datarootdir)/icons/hicolor/$${file#*/}; \
	done

install-icons:
	install -d $(DESTDIR)$(datarootdir)/applications
	install -m 0644 $(program_unix_name).desktop $(DESTDIR)$(datarootdir)/applications/$(program_unix_name).desktop


uninstall:
	set -e; for file in mplayer/*.py $$(find pycl pysd pytee subtitles -name '*.py'; find icons -name '*.png' -o -name '*.svg'); do \
		rm -f $(DESTDIR)$(data_dir)/$$file; \
	done
	set -e; while true; do \
		if [ $${removed:-1} -eq 0 ]; then \
			break; \
		fi; \
		removed=0; \
		if [ -d $(DESTDIR)$(data_dir) ]; then \
			for dir in $$(find $(DESTDIR)$(data_dir) -type d -empty); do \
				rmdir $$dir; let removed+=1; \
			done; \
		fi; \
	done
	rm -f $(DESTDIR)$(bindir)/$(program_unix_name)

uninstall-desktop:
	rm -f $(DESTDIR)$(datarootdir)/applications/$(program_unix_name).desktop

uninstall-icons:
	set -e; for file in $$(find icons -name '*.png' -o -name '*.svg'); do \
		rm -f $(DESTDIR)$(datarootdir)/icons/hicolor/$${file#*/}; \
	done


clean:
distclean: clean

