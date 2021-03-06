from math import comb as binomial
import pickle
import random
from collections import deque
from copy import copy

from codes.utils.definitions import *

# define scope of package
__all__ = [
    "get_aa_counts", "get_block_counts", "is_ambiguous", "is_promiscuous",
    "is_one_to_one", "get_codon_connectivity", "get_resi_connectivity",
    "get_codon_neighbors", "table_to_blocks", "blocks_to_table", "check_block",
    "random_code", "num_codes", "silencicity", "mutability", "promiscuity",
    "mut_pair_num", "get_mut_pairs", "order_NTPs",
]
def __dir__():
    default = [key for key in globals().keys() if key[:2] == '__']
    return default + __all__

def get_aa_counts(table):
    ''' A function that takes a Code and finds the counts of each
    AA. Returns a dictionary mapping AA to their respective counts.

    Parameters
    ----------
    dict table: a python dict representing the codon table

    Returns
    -------
    dict AA_count: a python dict mapping amino acids to degeneracy
    '''
    # declare dictionary of AA counts
    AA_count = {}
    # iterate over key and value pairs in self.table
    for codon, AA in table.items():
        # handle case where AA is previously uncounted
        if AA not in AA_count:
            # add AA to AA_count and initialize count value to 1
            AA_count[AA] = 1
        # else, increment AA count
        else:
            AA_count[AA] += 1
    # return AA_count dictionary
    return AA_count


def get_block_counts(blocks):
    ''' A function that takes a Code represented in block structure
    form and finds the number of blocks encoding each AA. Returns a
    dictionary mapping AA to their respective counts.

    Parameters
    ----------
    dict blocks: a python dict representing the codon table in block form

    Returns
    -------
    dict block_counts: a python dict mapping amino acids to degeneracy
    '''
    # initialize dict of counts and populate keys
    block_counts = {}
    for AA in residues:
        block_counts[AA] = 0
    # increment counts
    for AA in blocks.values():
        block_counts[AA] += 1
    # return block_counts
    return block_counts


def is_ambiguous(table):
    '''A staticmethod that takes a codon table as a dictionary and returns True if it is ambiguous and False if not.

    Parameters
    ----------
    dict table: a python dict representing the codon table

    Returns
    -------
    bool ambiguous: boolean representing the ambiguity of the table
    '''
    # use promiscuity method to determine ambiguity
    try:
        __ = promiscuity(table, allow_ambiguous=False)  # fails if ambiguous
        ambiguous = False
    except:
        ambiguous = True
    return ambiguous


def is_promiscuous(table):
    '''A staticmethod that takes a codon table as a dictionary and returns True if it represents a promiscuous table and False if not.

    Parameters
    ----------
    dict table: a python dict representing the codon table

    Returns
    -------
    bool ambiguous: boolean representing the promiscuity of the table
    '''
    # this is a one liner, but a tad obfuscated. Checks to see if each codon encodes for only one AA (thus is type str).
    # returns true if any of the elements are not strings
    return sum(type(AA) != str for AA in table.values()) > 0


def is_one_to_one(table):
    '''A staticmethod that takes a codon table as a dictionary and returns
        True if it represents a One-To-One genetic code and False otherwise.

        A one-to-one code is defined as a code in which every amino acid is
        represented with exactly one codon. This defines an unambiguous
        mapping of protein sequence to corresponding DNA sequence.

    Parameters
    ----------
    dict table: a python dict representing the codon table

    Returns
    -------
    bool one2one: boolean; True if One-To-One, and False otherwise
    '''
    # declare storage dict to count amino acid number
    aa_set = set(aa for aa in table.values())
    aa_counts = {aa: 0 for aa in aa_set}
    # count number of amino acids
    for aa in table.values():
        aa_counts[aa] += 1
    # iterate through dictionary and check counts
    one2one = True
    for aa, count in aa_counts.items():
        # skip stop and null signals:
        if aa in {'*', '0'}:
            continue
        elif count > 1:
            one2one = False
            break
    return one2one


def get_codon_connectivity(table):
    '''get_codon_connectivity(dict table) a function that takes a codon table
    and finds the graph distance between codon pairs. Connectivity is
    defined as follows: two codons c and c' are as connected if a series of
    point mutations can convert c to c' changing which amino acid it
    encodes for, until the last mutation (i.e. only) one AA change is
    allowed per path.

    Outputs a dict of str --> list of (str, int) tuples representing a list
    of the connected codons and their distance. Implemented as breadth
    first search.

    Parameters
    ----------
    dict table: a python dict representing the codon table

    Returns
    -------
    dict dist_dict: a python dictionary representing the adjacency matrix of
        a codon table with respect to codon neighbors.
    '''
    # declare dictionary of distances
    dist_dict = {}
    # loop through all possible codons
    for codon in table.keys():
        # declare temporary cache to hold discovered codons; store first codon in there
        cache = set(codon)
        # declare queue of codons to check
        codon_deque = deque()
        # declare neighbors list
        neighbors = []
        # use connect_recurse to map connectivity
        dist_dict[codon] = _connect_recurse(codon, 1, table,
                                                   neighbors, codon_deque, cache)
    # return codon_dist
    return dist_dict


def _connect_recurse(codon, level, table, neighbors, codon_deque, cache):
    ''' A recursive helper function that finds all of a codon's nearest
    neighbors and how far away they are. Returns a list of tuples
    representing the codons and their distances away.

    Codons are said to be connected if going from c --> c' converts the
    decoded AA from A --> A' without an intermediate residue.

    Parameters
    ----------
    - str codon: a string representing the input codon
    - int level: the current number of mutations away from the start codon
    - dict table: a python dict representing the codon table
    - list neighbors: the current list of the base codon's nearest neighbors
    - deque codon_deque: the queue of codons to search recursively
    - set cache: memoization set to store previously visited codons
    Returns
    -------
    list neighbors: returns updated neighbors list
    '''
    # import ipdb; ipdb.set_trace()
    # loop through every codon one mutation away
    for i, base in enumerate(codon):
        for nt in rNTPs:
            # handle if nt is the same as base
            if nt == base: continue
            # if not, generate new codon
            c_new = codon[:i] + nt + codon[i + 1:]
            # Base case: c_new already found
            if c_new in cache:
                continue
            # Base case: found terminus
            elif table[c_new] != table[codon]:
                # add distance to neighbors list
                neighbors.append((c_new, level))
                # add c_new to cache of found codons
                cache.add(str(c_new))
            # Recursive case
            else:
                # add c_new to cache of found codons
                cache.add(c_new)
                # append c_new to queue of codons to recurse through
                codon_deque.appendleft((c_new, level))
    # iterate over codons to recursively search for connectivity
    while not len(codon_deque) == 0:
        # get next codon to search
        c, newlevel = codon_deque.pop()
        # append results to neighbors list
        neighbors = _connect_recurse(c, newlevel + 1, table,
                                            neighbors, codon_deque, cache)
    # return resulting list
    return neighbors


def get_resi_connectivity(table):
    ''' get_resi_connectivity(dict table): a function that takes a dictionary
    representing a codon table and outputs a dictionary mapping amino acids
    to their respective neighbors, along with number of mutations away.
    '''
    # call get_codon_connectivity
    codon_dist_dict = get_codon_connectivity(table)
    # declare dict to return
    resi_dist_dict = {}
    # loop over codons
    for c1, codon_neighbors in codon_dist_dict.items():
        # extract amino acid for c1 and declare neighbors list
        A1 = table[c1]
        aa_neighbors = []
        # loop over elements of neighbors list
        for (c2, level) in codon_neighbors:
            # convert neighbors to residues and store
            A2 = table[c2]
            aa_neighbors.append((A2, level))
        # store resulting list in resi_dist_dict
        if A1 not in resi_dist_dict:
            resi_dist_dict[A1] = aa_neighbors
        else:
            resi_dist_dict[A1] += aa_neighbors
    # return dictionary
    return resi_dist_dict


def get_codon_neighbors(codon):
    '''A function used to get all codons one mutation away from the given codon.

    Parameters
    ----------
    str codon: the codon whose neighbors will be returned

    Returns
    -------
    list<str> neighbors: a list of codons one mutation away
    '''
    # declare list of neighbors
    neighbors = []
    # generate nearest neighbors by looping over codon positions
    for i, base in enumerate(codon):
        for nt in rNTPs:
            # handle if nt is the same as base
            if nt == base:
                continue
            # if not, generate new codon
            c_new = codon[:i] + nt + codon[i + 1:]
            # store new codon in neighbors
            neighbors.append(c_new)
    # return resulting list
    return neighbors


def table_to_blocks(table, block_struct):
    '''A function that takes a codon table and returns the
    representation as blocks of codons (individual tRNAs) as opposed to
    individual codons.

    Parameters
    ----------
    - dict table: a python dict representing the codon table
    - dict block_struct: a python dict representing the table block structure

    Returns
    -------
    - dict blocks: a python dict representing the codon table in block form
    - bool False: an "exception" if input table does not match block_struct
    '''
    # run check_block to confirm proper block structure, returns False if not
    if check_block(table, block_struct) != True:
        return False
    # declare dictionary to return
    blocks = {}
    # loop over block_struct and populate blocks
    for block_ind, codon_list in block_struct.items():
        blocks[block_ind] = table[codon_list[0]]
    # return populated blocks dict
    return blocks


def blocks_to_table(blocks, block_struct):
    '''A function that takes a codon table represented in block
    structure form and returns the representation as a traditional codon
    table

    Parameters
    ----------
        dict blocks: a python dict representing the codon table in block form
        dict block_struct: a python dict representing the table block structure

    Returns
    -------
        dict table: a python dict representing the codon table
        bool False: an "exception" if input table does not match block_struct
    '''
    # declare table to return
    table = {}
    # loop over blocks in block_struct and assign to table using blocks
    for block_ind, codon_list in block_struct.items():
        block_aa = blocks[block_ind]
        for codon in codon_list:
            table[codon] = block_aa
    # return filled codon table
    return table


def check_block(table, block_struct):
    '''A function used to check whether a given codon table conforms
    to the given block structure

    Parameters
    ----------
    - dict table: a python dict representing the codon table
    - dict block_struct: a python dict representing the table block structure

    Returns
    -------
    bool valid: true->table conforms to block structure; false otherwise
    '''
    # loop over codons in each block; return false if they code for
    # different residues
    for codon_list in block_struct.values():
        # initialize set of residues that a block codes for and populate
        block_residues = set()
        for codon in codon_list:
            block_residues.add(table[codon])
        # return false if the set is more than one element long
        if len(block_residues) > 1:
            return False
    # if function reaches this point, return True
    return True

def random_code(block_structure='standard'):
    '''A function used to generate a random codon table, optionally
    defining the block structure. Will guarantee each amino acid be
    represented by at least one block in the table.

    Parameters
    ----------
    str block_structure = 'standard': a string telling the simulator which
        wobble rules to follow for accepting new tables

    Acceptable inputs:
    - 'standard' : 48 blocks
    - 'preserve_block' : maintain same block structure as standard table
    - 'unrestricted' : 63 open blocks, at least 1 of every AA and stop.

    Returns
    -------
    dict table: a python dict representing the codon table to return
    '''
    # determine block structure based on wobble rule
    block_choices = {
        'standard': standard_block,
        'preserve_block': natural_block,
        'unrestricted': unrestricted_block
    }
    try:
        block_struct = copy(block_choices[block_structure])
    except:
        raise ValueError(
            'block_structure string not recognized. Use one of the following options: {0}'.format(
                set(block_choices.keys())
            )
        )
    # get blocks to assign
    blocks = list(block_struct.keys())
    random.shuffle(blocks)
    # randomly assign one block to each residue
    for AA in residues:
        block = blocks.pop()
        block_struct[block] = AA
    # randomly assign values to the remaining blocks
    for block in blocks:
        AA = random.choice(residues)
        block_struct[block] = AA
    # convert block_struct to table and return
    return blocks_to_table(block_struct, block_choices[block_structure])


def num_codes(l_aa, b):
    '''A function used to calculate the number of codon tables
    realizable given a number of amino acids to include, length of the
    codon, and number of blocks. Relies on an inclusion/exclusion criterion
    (i.e. count the total number of codon tables, minus the number that do
    not include one AA, plus the number that do not include two AAs...)

    l_aa = length of amino acid alphabet (20 + 1 stop)
    b = number of blocks to assign (triplet most permissive = 48, quadruplet most permissive = 192)

    n = l_aa^b + Sum_i^(l_aa-1) [(-1)^i * binomial(l_aa, i) * (l_aa - i)^b]

    Parameters
    ----------
    - int l_aa: the number of amino acids + Stop to encode
    - int b: the number of blocks in the codon table

    Returns
    -------
    - int n: the number of possible tables
    - str num: n, represented in scientific notation as a string
    '''
    # calculate n
    n = l_aa**b + np.array(
        [(-1)**i * binomial(l_aa,  i) * (l_aa - i)**b for i in range(1, l_aa)]
    ).sum()
    # handle string processing
    mag = -1
    temp_n = n
    while (temp_n > 0):
        # increment mag for each order of magnitude
        temp_n = temp_n // 10
        mag += 1
    # create string representing n in scientific notation
    str_n = str(n)[:3]
    num = '{0}.{1}E{2}'.format(str_n[0], str_n[1:], mag)
    return n, num


def silencicity(table):
    '''A function used to calculate the silencicity of a codon table.
    Silencicity is a lab defined metric calculating the fraction of all
    mutations that are synonymous out of all possible ones.

    Parameters
    ----------
    dict table: a python dict representing the codon table to analyze

    Returns
    -------
    float silencicity: a float representing the silencicity metric
    '''
    # initialize counter and get mutation pairs
    syn_mut = 0
    mut_pairs = get_mut_pairs(table)
    total_mut = len(mut_pairs)
    # loop over mutation pairs and increment for synonymous mutations
    for (c1, c2) in mut_pairs:
        if (table[c1] == table[c2]):
            syn_mut += 1
    # return fraction of synonymous mutations
    return syn_mut / total_mut


def mutability(table):
    '''A function used to calculate the average chemical variability
    of single point mutations in a given genetic code. For each
    nonsynonymous single point mutation, it calculates the chemical
    distance between the previously encoded amino acid and its replacement
    after mutation. The mean of these values is then returned.

    Parameters
    ----------
    dict table: a python dict representing the codon table to analyze

    Returns
    -------
    float mutability: a float representing the silencicity metric
    '''
    # initialize counter and running metric, and get mutation pairs
    nonsyn_mut = 0
    metric = 0
    mut_pairs = get_mut_pairs(table)
    total_mut = len(mut_pairs)
    # get Kyte-Doolittle hydropathy metric
    kd = kd_hydropathy
    # loop over mutation pairs
    for (c1, c2) in mut_pairs:
        # increment counter and metric if nonsynonymous
        if not (table[c1] == table[c2]):
            # increment counter
            nonsyn_mut += 1
            # increment metric
            aa1 = table[c1]
            aa2 = table[c2]
            metric += np.abs(kd[aa1] - kd[aa2])
    # if there are no nonsynonymous mutations, return 0
    if nonsyn_mut == 0:
        mutability = 0
    # else, return the average dKD per mutation
    else:
        mutability = metric / nonsyn_mut
    return mutability


def promiscuity(table, allow_ambiguous=False):
    '''A function used to generate the genetic code resulting from
    considering tRNA promiscuity. Uses Crick Wobble Hypothesis. Raises an
    exception if the table generated is ambiguous (more than one signal
    acceptable for a given codon)

    Parameters
    ----------
    - dict table: the codon table to promsicuitize
    - bool allow_ambiguous: flag telling code whether to accept ambiguity

    Returns
    -------
    dict promsicuous: the resulting table when considering tRNA promiscuity
    '''
    # handle type errors for input table
    if type(table) != dict:
        try:
            table = table.codon_dict  # attempt to convert to dict
        except:
            raise ValueError("Input table is not type dict or CodonTable")
    # declare table to return
    promiscuous = {}
    for codon in triplet_codons:
        promiscuous[codon] = '0'
    # loop over codons to reassign
    for codon, AA in table.items():
        # skip assignments to STOP
        if AA == '0': continue
        # get codons that would be decoded in reality
        wobble = wobble_WC[basepair_WC[codon[-1]]]
        codons = [codon[:2] + nt3 for nt3 in wobble]
        # determine if there is ambiguity
        acceptable = [AA, '0']
        for c in codons:
            if promiscuous[c] not in acceptable:
                # raise error if allow_ambiguous = False
                if not allow_ambiguous:
                    raise ValueError('input code generates ambiguous code upon promiscuization')
                else:
                    # else, package all nonstop codons as tuple
                    AAs = tuple(
                        [aa for aa in promiscuous[c] if aa != '0'] +
                        [AA]
                    )
                    promiscuous[c] = AAs
            # otherwise, package as simple str --> str mapping
            else:
                promiscuous[c] = AA
    return promiscuous


def mut_pair_num(table):
    '''
    A function that calculates the number of pairs of codons one
    mutation away from each other. Treats mutations with directionality. In
    general, the number of mutational pairs is equal to the number of
    codons in a table multiplied by the number of unique codons within one
    mutation. Let a = alphabet length (generally 4), l = codon length
    (generally 3)

            n = (a^l) * l(a-1)

    Parameters
    ----------
    dict table: the codon table to analyze

    Returns
    -------
    int mut_num: the number of distinct mutational pairs.
    '''
    # get list of all codons in table
    codon_list = list(table)
    # get alphabet size
    alphabet = set()
    for codon in codon_list:
        for nt in codon:
            alphabet.add(nt)
    a = len(alphabet)
    # get codon length
    l = len(codon_list[0])
    # calculate mut_num and return
    return (a ** l) * l * (a - 1)


def get_mut_pairs(table):
    '''
    A function used to generate the set of all pairs of codons one
    mutation away given a codon table.

    Parameters
    ----------
    dict table: the codon table to analyze

    Returns
    -------
    set<(str, str)> mut_pairs: a set of distinct mutational pairs.
    '''
    # declare set of mutational pairs
    mut_pairs = set()
    # get list of codons and iterate over them
    codon_list = list(table)
    for codon in codon_list:
        # iterate over each base in the codon
        for i, base in enumerate(codon):
            for nt in rNTPs:
                # handle if nt is the same as base
                if nt == base:
                    continue
                # if not, generate new codon
                c_new = codon[:i] + nt + codon[i + 1:]
                # add to set
                mut_pairs.add((codon, c_new))
    return mut_pairs


def order_NTPs(sortable, nucleic_acid='RNA'):
    '''A function used to sort iterables by standard order of NTPs.
    For RNA, U-C-A-G. For DNA, T-C-A-G. Returns sorted object.

    Parameters
    ----------
    - iterable sortable: the object to sort
    - str nucleic_acid: the type of nucleic acid considered

    Returns
    -------
    iterable sorted_obj: the sorted object
    '''
    # define ordering dictionary
    orderdict = {
        'RNA': ['U', 'C', 'A', 'G'],
        'DNA': ['T', 'C', 'A', 'G']
    }
    # raise error if nucleic_acid flag invalid
    if nucleic_acid.upper() not in orderdict:
        raise ValueError('nucleic_acid flag set to invalid option (use DNA or RNA)')
    # attempt sorting
    try:
        order = orderdict[nucleic_acid.upper()]
        sorted_obj = sorted(
            sortable, key=lambda word: [order.index(nt) for nt in word]
        )
    except ValueError:
        print('Variable to sort broke the code :/')
        # raise error
        sorted_obj = False
    return sorted_obj

if __name__ == '__main__':
    pass
