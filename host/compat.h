#ifndef TEGRARCM_COMPAT_H
#define TEGRARCM_COMPAT_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <stdarg.h>
#ifdef _WIN32
#include <windows.h>
#endif

#ifndef MIN
#define MIN(a,b) ((a) < (b) ? (a) : (b))
#endif

static inline void error(int status, int errnum, const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
    if (errnum)
        fprintf(stderr, ": %s", strerror(errnum));
    fprintf(stderr, "\n");
    if (status)
        exit(status);
}

#endif
