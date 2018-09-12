import itertools

from python_log_indenter import IndentedLoggerAdapter
import logging
import spacy
nlp=spacy.load('en_core_web_sm')

class AnswerBot:
    def __init__(self,debug=True):
        #logging setup
        logger=logging.getLogger(__name__)

        formatter=logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s', datefmt='%H:%M')
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        self.log=IndentedLoggerAdapter(logger)
        self.log.setLevel(logging.DEBUG if debug else logging.WARNING)

    @staticmethod
    def fix_question(text:str):
        if text.endswith('.'):
            text=text[:-1]
        if not text.endswith('?'):
            text=text+'?'
        return text[0].upper()+text[1:]

    def parse_question(self,text):
        """
        breaks down a natural-language query into a hierarchical structure
        :return: queries:[parts:[token]]
        """
        doc=nlp(self.fix_question(text))
        self.log.debug(str(doc.print_tree()))
        self.log.info("parsing question: "+str(doc))
        self.log.add()

        ret=[]
        for sent in doc.sents:
            ret.extend(self.parse_sent(sent))
        self.log.sub()
        self.log.info(str(ret))
        return ret

    def parse_sent(self, sent):
        self.log.info("parsing sent: "+str(sent))
        return [self.parse_span(sent)]

    def parse_span(self,span):
        self.log.info("parsing span: "+str(span))
        self.log.add()
        ret = self.parse_children(span.root)
        self.log.sub()
        self.log.info("<<"+str(ret))
        return ret

    def parse_children(self,root,skip_root=False):
        self.log.info("parsing: "+str(root))
        self.log.add()

        ret=[]

        # which tokens to append,prepend and ignore
        deps=[
                # children tokens to ignore
                [
                  'case',
                  'punct',
                  'det',
                  'auxpass',
                  # do not ignore advmod
                ],
                # children tokens to be prepended (to the ROOT)
                [
                    'nsubj',
                    'poss',
                   'acl',
                   'advcl',
                   'relcl',
                   'compound',
                   'attr',
                ],
                # children tokens to be prepended but the children themselves omitted (grandchildren only)
                [
                    'prep',
                    'agent'
                    # 'advmod',
                ],
                # appended
                [
                    'pobj',
                    'amod',
                    'nsubjpass',
                    'pcomp',
                    'acomp',
                    'oprd',
                    'appos',
                ],
                #appending skip
                [
                    # 'prep',
                ],
            ]

        # before root
        for child in root.children:
            if child.dep_ in deps[0]:
                continue
            elif child.dep_ in deps[2]:
                ret.extend(self.parse_children(child,skip_root=True))
            elif child.dep_ in deps[1]:
                ret.extend(self.parse_children(child))
            # special case
            elif child.dep_=='dobj':
                ret.extend(self.parse_children(child,skip_root=child.tag_=='WDT'))

        if not skip_root:
            if root.pos_!='VERB' and root.pos_!='ADP':
                if not root.dep_ in deps[0]:
                    ret.append(root)

        # after root
        for child in root.children:
            if child.dep_ in deps[0]:
                continue
            elif child.dep_ in deps[4]:
                ret.extend(self.parse_children(child,skip_root=True))
            elif child.dep_ in deps[3]:
                ret.extend(self.parse_children(child))

        self.log.sub()
        self.log.info("<<"+str(ret))
        return ret

    @staticmethod
    def get_query_combs(query):
        """
        :return: list of combinations of splitting up the query
        """
        # want to get every combination of how to split up the entries in a list
        # way of representing the commas: 0=no comma, 1=comma
        # We want the binary combinations of length `(amount of entries)-1`
        # which indicate to whether to have a 'comma' at each point between the entries
        # ---
        # Example: consider the lists A and B
        # 0  1  2  3 <-- A: entries
        #  0  1   2  <-- B: can be thought of as positions for commas.
        # to get every combination of how to split up the entries in A
        # (like [0123],[012,3],[01,23],[01,2,3] etc)
        # you must get every arrangement of B (the commas in-between the entries)
        # let's say 0 = no comma, 1 = comma
        # the possible arrangements of B will be
        # 001,010,011,101,110,111
        # this is the binary pattern

        ret=[]
        for split_config in itertools.product([0,1],repeat=len(query)-1):
            obuf=[]
            buf=[]
            for i in range(len(split_config)):
                buf.append(query[i])
                if split_config[i]: # if there is a 'comma' after the entry
                    #flush buf to obuf
                    obuf.append(buf)
                    buf=[]
            buf.append(query[-1]) # last item will never 'have a comma' after it
            obuf.append(buf) # flush buf to obuf
            ret.append(obuf) # flush obuf to ret
        return ret

    def select_pages(self, queries):
        """
        :return: relevant URLs for pages (verified to exist), given queries
        """
        pass

if __name__=='__main__':
    # print(AnswerBot.get_query_combs('abcd'))
    AnswerBot().parse_question("Who is Obama's Dad")
    # todo list:
    # Where was Obama born?