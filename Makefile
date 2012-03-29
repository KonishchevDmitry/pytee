.PHONY: all install uninstall clean distclean

PREFIX := /usr
bindir := $(PREFIX)/bin
datarootdir := $(PREFIX)/share

program_unix_name := pytee
data_dir := $(datarootdir)/$(program_unix_name)

all:

install: all
	set -e; \
	for file in $$(find mplayer pycl pysd pytee subtitles -name '*.py'; find icons -name '*.png' -o -name '*.svg'); do \
		install -d $(DESTDIR)$(data_dir)/$$(dirname $$file); \
		install -m 0644 $$file $(DESTDIR)$(data_dir)/$$file; \
	done; \
	if [ "$$(uname -s)" != "Darwin" ]; then \
		for file in $$(find icons -name '*.png' -o -name '*.svg'); do \
			install -d $(DESTDIR)$(datarootdir)/icons/hicolor/$$(dirname $${file#*/}); \
			install -m 0644 $$file $(DESTDIR)$(datarootdir)/icons/hicolor/$${file#*/}; \
		done; \
		install -d $(DESTDIR)$(datarootdir)/applications; \
		install -m 0644 $(program_unix_name).desktop $(DESTDIR)$(datarootdir)/applications/$(program_unix_name).desktop; \
	fi
	install -d $(DESTDIR)$(bindir);
	echo '#!/bin/sh\nexec $(data_dir)/$(program_unix_name)/main.py "$$@"' > $(DESTDIR)$(bindir)/$(program_unix_name);
	chmod a+x $(DESTDIR)$(data_dir)/$(program_unix_name)/main.py;
	chmod a+x $(DESTDIR)$(bindir)/$(program_unix_name);

uninstall:
	set -e; \
	for file in $$(find mplayer pycl pysd pytee subtitles -name '*.py'; find icons -name '*.png' -o -name '*.svg'); do \
		rm -f $(DESTDIR)$(data_dir)/$$file; \
	done; \
	while true; do \
		if [ $${removed:-1} -eq 0 ]; then \
			break; \
		fi; \
		removed=0; \
		if [ -d $(DESTDIR)$(data_dir) ]; then \
			for dir in $$(find $(DESTDIR)$(data_dir) -type d -empty); do \
				rmdir $$dir; let removed+=1; \
			done; \
		fi; \
	done; \
	if [ "$$(uname -s)" != "Darwin" ]; then \
		for file in $$(find icons -name '*.png' -o -name '*.svg'); do \
			rm -f $(DESTDIR)$(datarootdir)/icons/hicolor/$${file#*/}; \
		done; \
		rm -f $(DESTDIR)$(datarootdir)/applications/$(program_unix_name).desktop; \
	fi
	rm -f $(DESTDIR)$(bindir)/$(program_unix_name)

clean:
distclean: clean

