## Plan Recognition over Plan Libraries as Planning

**DISCLAIMER**: This is very a very old codebase (7 years and counting) so it
may be a bit hard to get it up and running. It used an old version of ANTLR (version 3)
and Python [NLTK](http://www.nltk.org/book_1ed/).

### Usage Notes

There are two: ```parse.py``` and ```recognize_plan.py```. Both of them are self--documenting.
Besides that, in the folder ```solvers``` you will find very old versions of the FF, Metric FF
and LAMA planners. These are used off-the-shelf by the scripts, and you'll need to edit the
code in order to change which planner is to be used.
