#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# (C) 2018 Dublin City University
# All rights reserved. This material may not be
# reproduced, displayed, modified or distributed without the express prior
# written permission of the copyright holder.

# Author: Joachim Wagner

# This implements the combination method described in
# Attardi and Dell'Orletta (2009) Reverse Revision and Linear Tree
# Combination for Dependency Parsing. Proc. NAACL pp 261-264 N09-2066.

import common
import sys

def print_parse(out, parse):
    # pretty print parse for debugging
    for comment_line in parse[1]:
        out.write(comment_line+'\n')
    column2maxlength = {}
    for word_fields in parse[0]:
        for i, v in enumerate(word_fields):
            if i in column2maxlength:
                column2maxlength[i] = max(len(v), column2maxlength[i])
            else:
                column2maxlength[i] = len(v)
    for word_fields in parse[0]:
        columns = []
        for i, v in enumerate(word_fields):
            format_str = '%%-%ds' %(column2maxlength[i])
            columns.append(format_str %v)
        out.write('\t'.join(columns))
        out.write('\n')
    out.write('\n')

def populate_arcs_available(arcs_available, parses, prune_label = False, weights = None):
    for p_index, parse in enumerate(parses):
        if weights:
            weight = weights[p_index]
        else:
            weight = 1
        preceeding_lines = []
        word_lines = parse[0]
        num_lines = len(word_lines)
        last_arc = None
        for line_index, parse_line in enumerate(word_lines):
            head = parse_line[common.HEAD]
            if head == '_':
                # store word lines that are not part of the parse, such as
                # multi-word lines, so that we can re-produce them in the
                # combined output
                preceeding_lines.append('\t'.join(parse_line))
            else:
                child = parse_line[common.ID]
                try:
                    label = parse_line[common.DEPREL]
                except IndexError:
                    sys.stderr.write('Error: too few fields in parse:\n')
                    print_parse(sys.stderr, parse)
                    raise ValueError, 'no DEPREL field in parse line'
                if prune_label and ':' in label:
                    label = label[:label.find(':')]
                arc = (head, child, label)
                rank = line_index / float(num_lines)
                if arc not in arcs_available:
                    empty_list_1 = []
                    empty_list_2 = []
                    empty_list_3 = []
                    arcs_available[arc] = [
                        0, 0.0, empty_list_1, empty_list_2, empty_list_3
                    ]
                arc_info = arcs_available[arc]
                arc_info[0] += weight
                arc_info[1] += rank
                arc_info[2].append('\t'.join(parse_line))
                arc_info[3].append('\n'.join(preceeding_lines))
                arc_info[4].append('')
                last_arc = arc
                preceeding_lines = []
        if preceeding_lines:
            if last_arc:
                # update last arc's trailing lines
                arc_info = arcs_available[last_arc]
                arc_info[4][-1] = '\n'.join(preceeding_lines)
            else:
                sys.stderr.write('Warning: ignoring unbound multi-token lines')
                sys.stderr.write(' in the following parse:\n')
                print_parse(sys.stderr, parse)

def populate_fringe(arcs_in_fringe, arcs_available):
    moved = []
    for arc in arcs_available:
        if arc[0] == '0':
            arcs_in_fringe[arc] = arcs_available[arc]
            moved.append(arc) # defer deletion
    for arc in moved:
        del arcs_available[arc]

def select_arc_from_fringe(arcs_in_fringe, arcs_in_tree, hexsalt = '', old_tiebreaker = False, debug = False):
    if debug:
        sys.stderr.write('select_arc_from_fringe() %d arc(s) in fringe and %d arc(s) in tree\n' %(len(arcs_in_fringe), len(arcs_in_tree)))
    best_priority = (-1, -1, -1, '', 0.0)
    best_arc    = None
    for arc in arcs_in_fringe:
        if debug:
            sys.stderr.write('\tfringe arc %r with weight %.6f\n' %(arc, arcs_in_fringe[arc][0]))
        suitable = False
        if not arcs_in_tree:
            suitable = True
        else:
            head = arc[0]
            for tree_arc in arcs_in_tree:
                if tree_arc[1] == head:
                    suitable = True
                    break
        if suitable:
             weight = arcs_in_fringe[arc][0]
             local_priority = common.get_tiebreaker(hexsalt, arc, old_tiebreaker)
             priority = (
                 weight,
                 local_priority,
                 arc  # for the unlikely case of a hash collision
             )
             if priority > best_priority:
                 if debug:
                     sys.stderr.write('\t\tnew best\n')
                 best_priority = priority
                 best_arc    = arc
        elif debug:
            sys.stderr.write('\t\tnot suitable\n')
    return best_arc

def delete_arcs_with_child(arcs, child):
    remove_me = []
    for arc in arcs:
        if arc[1] == child:
            # defer deletion as python is not
            # happy with dictionary changes while
            # iterating its keys
            # https://stackoverflow.com/questions/5384914/how-to-delete-items-from-a-dictionary-while-iterating-over-it
            # https://stackoverflow.com/questions/9023078/custom-dict-that-allows-delete-during-iteration
            remove_me.append(arc)
    for arc in remove_me:
        del arcs[arc]

def add_arcs_to_fringe(arcs_in_fringe, arcs_in_tree, arcs_available):
    remove_me = []
    for arc in arcs_available:
        head, child, _ = arc
        found_head_in_tree = False
        child_already_covered = False
        for tree_arc in arcs_in_tree:
            tree_arc_child = tree_arc[1]
            if head == tree_arc_child:
                found_head_in_tree = True
            if child == tree_arc_child:
                child_already_covered = True
                break
        if found_head_in_tree and not child_already_covered:
           arcs_in_fringe[arc] = arcs_available[arc]
           remove_me.append(arc)
    for arc in remove_me:
        del arcs_available[arc]

def select_most_frequent(list_of_strings, hexsalt = '', old_tiebreaker = False, debug = False):
    string2freq = {}
    for s in list_of_strings:
        if s not in string2freq:
            string2freq[s] = 0
        string2freq[s] = string2freq[s] + 1
    highest_priority = (-1, '', 0.0)
    context = common.get_tiebreaker(hexsalt, sorted(list_of_strings), old_tiebreaker)
    selected_s = ''
    for s in string2freq:
        freq = string2freq[s]
        local_priority   = common.get_tiebreaker(hexsalt, [s], old_tiebreaker)
        context_priority = common.get_tiebreaker(hexsalt, [s, context], old_tiebreaker)
        priority = (
             freq,
             local_priority,
             context_priority,
             s  # for the unlikely case of two hash collisions
        )
        if priority > highest_priority:
            selected_s = s
            highest_priority = priority
    return selected_s


def get_word_lines_from_tree(arcs_in_tree, hexsalt = '', old_tiebreaker = False, debug = False):
    rank_and_details = []
    for arc in arcs_in_tree:
        _, rank, lines, preceeding_lines, trailing_lines = arcs_in_tree[arc]
        rank = rank / float(len(lines))
        selected_line = select_most_frequent(lines, hexsalt, old_tiebreaker, debug)
        selected_preceeding_lines = select_most_frequent(preceeding_lines, hexsalt, old_tiebreaker, debug)
        selected_trailing_lines = select_most_frequent(trailing_lines, hexsalt, old_tiebreaker, debug)
        rank_and_details.append((
            rank,
            selected_line,
            selected_preceeding_lines,
            selected_trailing_lines
        ))
    rank_and_details.sort()
    retval = []
    trailing = []
    for _, parse_line, preceeding_lines, trailing_lines in rank_and_details:
        # parse lines that preceed the line with head
        if preceeding_lines:
            preceeding_lines = preceeding_lines.split('\n')
            for preceeding_line in preceeding_lines:
                retval.append(preceeding_line.split('\t'))
        # parse line with head
        retval.append(parse_line.split('\t'))
        # trailing parse line without head
        if trailing_lines:
            trailing_lines = trailing_lines.split('\n')
            for trailing_line in trailing_lines:
                # defer to after the last parse line with head
                trailing.append(trailing_line.split('\t'))
    for line in trailing:
        retval.append(line)
    return retval

def combine(parses, prune_label = False, weights = None,
    check_for_leftover_arcs = False, salt = None,
    old_tiebreaker = False, debug = False
):
    print_final_parse_to_stderr = False
    hexsalt = common.get_hexsalt(salt)
    if debug:
        sys.stderr.write('prune_label = %r\n' %prune_label)
        sys.stderr.write('weights     = %r\n' %weights)
        sys.stderr.write('hexsalt     = %r\n' %hexsalt)
        sys.stderr.write('old_tiebreaker = %r\n' %old_tiebreaker)
    # the following map arcs to
    # [weight, rank, list of lines, list of preceeding lines]
    arcs_in_tree   = {}
    arcs_in_fringe = {}
    arcs_available = {}
    # populate arcs_available
    populate_arcs_available(arcs_available, parses, prune_label, weights)
    # populate fringe with the set of arcs (head, child, label)
    # for which head is the root node 0
    populate_fringe(arcs_in_fringe, arcs_available)
    # grow the tree
    while arcs_in_fringe:
        # select arc from fringe to add to tree
        best_arc = select_arc_from_fringe(
            arcs_in_fringe, arcs_in_tree, hexsalt,
            old_tiebreaker, debug
        )
        if not best_arc:
            sys.stderr.write('Warning: no suitable arc')
            sys.stderr.write('\n\tfor tree %r' %arcs_in_tree.keys())
            sys.stderr.write('\n\tin fringe %r' %arcs_in_fringe.keys())
            sys.stderr.write('\n\tfor parses:\n')
            for parse in parses:
                print_parse(sys.stderr, parse)
            print_final_parse_to_stderr = True
            break
        # add best_arc to tree
        arcs_in_tree[best_arc] = arcs_in_fringe[best_arc]
        del arcs_in_fringe[best_arc]
        # remove all other arcs with this child from fringe
        # as we are done with finding the head for this child
        delete_arcs_with_child(arcs_in_fringe, best_arc[1])
        if check_for_leftover_arcs:
            # if we later want to check for leftover arcs
            # in arcs_available we need to clean up in
            # there as well
            delete_arcs_with_child(arcs_available, best_arc[1])
        # add arcs to the fringe
        add_arcs_to_fringe(arcs_in_fringe, arcs_in_tree, arcs_available)
    # sanity check
    if check_for_leftover_arcs and arcs_available:
        sys.stderr.write('Warning: empty fringe')
        sys.stderr.write(' but still arcs %r' %(arcs_available.keys()))
        sys.stderr.write(' available in the following parses:\n')
        for parse in parses:
            print_parse(sys.stderr, parse)
    # sort children into order
    new_word_lines = get_word_lines_from_tree(
        arcs_in_tree, hexsalt, old_tiebreaker, debug
    )
    # merge all comments
    comments = common.combine_comments(parses)
    retval = new_word_lines, comments
    if print_final_parse_to_stderr:
        sys.stderr.write('Returning parse:\n')
        print_parse(sys.stderr, retval)
    return retval

