.PHONY: all install uninstall clean distclean

PREFIX := /usr
bindir := $(PREFIX)/bin
datarootdir := $(PREFIX)/share

program_unix_name := pytee
data_dir := $(datarootdir)/$(program_unix_name)

all:

install: all
	for file in $$(find cl mplayer pysd pytee subtitles -name '*.py'; find icons -name '*.png' -o -name '*.svg'); do \
		install -m 0644 -D $$file $(DESTDIR)$(data_dir)/$$file; \
	done
	for file in $$(find icons -name '*.png' -o -name '*.svg'); do \
		install -m 0644 -D $$file $(DESTDIR)$(datarootdir)/icons/hicolor/$${file#*/}; \
	done
	install -m 0644 -D $(program_unix_name).desktop $(DESTDIR)$(datarootdir)/applications/$(program_unix_name).desktop
	mkdir -p $(DESTDIR)$(bindir)
	echo '#!/bin/sh\nexec $(data_dir)/$(program_unix_name)/main.py "$$@"' > $(DESTDIR)$(bindir)/$(program_unix_name)
	chmod a+x $(DESTDIR)$(data_dir)/$(program_unix_name)/main.py
	chmod a+x $(DESTDIR)$(bindir)/$(program_unix_name)

uninstall:
	for file in $$(find cl mplayer pysd pytee subtitles -name '*.py'; find icons -name '*.png' -o -name '*.svg'); do \
		rm -f $(DESTDIR)$(data_dir)/$$file; \
	done
	for dir in $$(find $(DESTDIR)$(data_dir) -type d | sort -r); do \
		rmdir --ignore-fail-on-non-empty $$dir; \
	done
	for file in $$(find icons -name '*.png' -o -name '*.svg'); do \
		rm -f $(DESTDIR)$(datarootdir)/icons/hicolor/$${file#*/}; \
	done
	rm -f $(DESTDIR)$(datarootdir)/applications/$(program_unix_name).desktop
	rm -f $(DESTDIR)$(bindir)/$(program_unix_name)

clean:
distclean: clean

