#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# (C) 2018 Dublin City University
# All rights reserved. This material may not be
# reproduced, displayed, modified or distributed without the express prior
# written permission of the copyright holder.

# Author: Joachim Wagner

import hashlib
import random

# Columns according to http://universaldependencies.org/format.html
ID     = 0   # Word index, integer starting at 1 for each new sentence; may be a range for multiword tokens; may be a decimal number for empty nodes.
FORM   = 1   # Word form or punctuation symbol.
LEMMA  = 2   # Lemma or stem of word form.
UPOS   = 3   # Universal part-of-speech tag.
XPOS   = 4   # Language-specific part-of-speech tag; underscore if not available.
FEATS  = 5   # List of morphological features from the universal feature inventory or from a defined language-specific extension; underscore if not available.
HEAD   = 6   # Head of the current word, which is either a value of ID or zero (0).
DEPREL = 7   # Universal dependency relation to the HEAD (root iff HEAD = 0) or a defined language-specific subtype of one.
DEPS   = 8   # Enhanced dependency graph in the form of a list of head-deprel pairs.
MISC   = 9   # Any other annotation.

debug = False

def combine_comments(parses):
    global debug
    comment2ranks = {}
    for _, comment_lines in parses:
        num_comments = len(comment_lines)
        if debug:
            comment2ranks['# %d comments' %num_comments] = [0.0]
        for index, comment in enumerate(comment_lines):
            if num_comments == 1:
                rank = 0.5
            else:
                rank = index / float(num_comments-1)
            if comment not in comment2ranks:
                comment2ranks[comment] = []
            comment2ranks[comment].append(rank)
    avgrank_and_comment = []
    for comment in comment2ranks:
        ranks = comment2ranks[comment]
        avgrank = sum(ranks) / float(len(ranks))
        avgrank_and_comment.append((avgrank, comment))
    avgrank_and_comment.sort()
    retval = []
    for _, comment in avgrank_and_comment:
        retval.append(comment)
    return retval

def get_hexsalt(salt):
    if not salt:
        data = 'r:%d' %random.getrandbits(640)
    elif type(salt) == str:
        data = 's:%s' %salt
    elif type(salt) in (int, long):
        data = 'i:%d' %salt
    elif type(salt) == float:
        data = 'f:%d' %hash(salt)
    else:
        data = 'h:%d' %hash(salt)
    return hashlib.sha512(data).hexdigest()

def get_tiebreaker(salt, items, old_tiebreaker = False):
    h = hashlib.sha512(salt)
    for item in items:
        h.update('%d:' %len(item))
        h.update(item)
    if old_tiebreaker:
        h.update('r:%d' %random.getrandbits(640))
    return h.hexdigest()

