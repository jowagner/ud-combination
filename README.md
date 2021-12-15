# Linear combination of UD basic parse trees for parser ensembles

This implements the combination method described in

[Giuseppe  Attardi](https://github.com/attardi "Github Profile")  and
[Felice  Dell'Orletta](https://scholar.google.com/citations?user=uhInFTQAAAAJ "Google Scholar Page").
2009.
[Re-verse revision and linear tree combination for dependency parsing](https://www.aclweb.org/anthology/N09-2066/ "View in ACL Anthology").
In *Proceedings of Human Language Technologies: The 2009 Annual Conference of the North American Chapter of the Association for Computational Linguistics, Companion Volume: ShortPapers*, pages 261–264, Boulder, Colorado.
Association for Computational Linguistics.

If you use this code please also cite
the following paper
in which
experiments using this code are first published.

[James Barry](https://github.com/jbrry/ "Github Profile"),
[Joachim Wagner](https://github.com/jowagner/ "Github Profile") and
[Jennifer Foster](https://github.com/fosterjen/ "Github Profile").
2020.
[The ADAPT Enhanced Dependency Parser at the IWPT 2020 Shared Task](https://www.aclweb.org/anthology/2020.iwpt-1.24/ "View in ACL Anthology").
In *Proceedings of the 16th International Conference on Parsing Technologies and the IWPT 2020 Shared Task on Parsing into Enhanced Universal Dependencies*,
pages 227–235. Online.
Association for Computational Linguistics.
DOI: 10.18653/v1/2020.iwpt-1.24


Run `combine.py --help` for usage.

## Output Instability

Footnote 12 of [Wagner et al. (2021) Revisiting Tri-training of Dependency Parsers](https://aclanthology.org/2021.emnlp-main.745/) points out that the way how ties are resolved that
occur in the greedy search of the combiner can effect the output quite a lot.
In their work, only three parsers are combined and they resort to running the
combiner multiple times
with different initialisation (option `--seed`)
and reporting average LAS.
