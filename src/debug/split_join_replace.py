#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Copyright 2014 The LogikSim Authors. All rights reserved.
Use of this source code is governed by the GNU GPL license that can
be found in the LICENSE.txt file.
'''

import itertools
import re
import timeit


def repl_rex(text, replacements):
    pattern = '|'.join(re.escape(pat) for pat in replacements)
    return re.sub(pattern, lambda m: replacements[m.group()], text)


def repl_rec_broken(text, replacements):
    replacements = replacements.copy()
    print()

    def rec_repl(text_, key, value):
        print(replacements, end=' ')
        print('text_=%r   key=%r   value=%r, text_.split(key)=%s' % (text_, key, value, text_.split(key)))
        try:
            item = replacements.popitem()
        except KeyError:
            return text_.replace(key, value)
        else:
            f = lambda x: rec_repl(x, *item)
            return value.join(map(f, text_.split(key)))

    return rec_repl(text, *replacements.popitem())


def repl_rec(text, replacements):
    def rec_repl(text_, key, irep):
        try:
            next_key = next(irep)
        except StopIteration:
            return text_.replace(key, replacements[key])
        else:
            f = lambda x, irep: rec_repl(x, next_key, irep)
            splits = text_.split(key)
            return replacements[key].join(map(f, splits, itertools.tee(irep, len(splits))))

    irep = iter(replacements)
    return rec_repl(text, next(irep), irep)


if __name__ == '__main__':
    s = "ab de ke de ab jk";
    d = {'a': 'de', 'de': 'a'};
    res = "deb a ke a deb jk"
    assert repl_rex(s, d) == res, repl_rex(s, d)
    assert repl_rec(s, d) == res, repl_rec(s, d)

    s = 'Ki KI';
    d = {'r': 's', 'Ki': 'KI', 'KI': 'ki'};
    res = 'KI ki'
    assert repl_rex(s, d) == res, repl_rex(s, d)
    assert repl_rec(s, d) == res, repl_rec(s, d)

    print('done')

    # profile both functions
    ti = lambda stat, n=100000: min(timeit.repeat(stat,
                                                  "from __main__ import repl_rec, repl_rex; "
                                                  "s = 'ab de ke de ab jk'; "
                                                  "d = {'a': 'de', 'de': 'a'}",
                                                  repeat=3, number=n))

    print(ti('repl_rex(s, d)'))
    print(ti('repl_rec(s, d)'))
