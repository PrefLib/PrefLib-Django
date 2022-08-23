from django.core.management.base import BaseCommand

from preflibapp.models import Metadata, DataTag
from preflibapp.choices import *


def initialize_tags():
    election_tag, _ = DataTag.objects.update_or_create(
        name="Election",
        defaults={
            "description": "The preferences apply to scenario in which some alternatives are to be selected",
            "parent": None
        }
    )

    sport_tag, _ = DataTag.objects.update_or_create(
        name="Sport",
        defaults={
            "description": "The data represent sport tournaments, interpreted as elections",
            "parent": election_tag
        }
    )

    politics_tag, _ = DataTag.objects.update_or_create(
        name="Politics",
        defaults={
            "description": "The preferences apply to political scenario",
            "parent": election_tag
        }
    )

    matching_tag, _ = DataTag.objects.update_or_create(
        name="Matching",
        defaults={
            "description": "The preferences apply to scenario in which alternatives are to be matched",
            "parent": None
        }
    )

    ratings_tag, _ = DataTag.objects.update_or_create(
        name="Ratings",
        defaults={
            "description": "The preferences express ratings about the alternatives",
            "parent": None
        }
    )

    combi_tag, _ = DataTag.objects.update_or_create(
        name="Combinatorial",
        defaults={
            "description": "The data represent combinatorial preferences about the alternatives.",
            "parent": None
        }
    )


def initialize_metadata():
    metadata_num_alt, _ = Metadata.objects.update_or_create(
        name="Number of alternatives",
        defaults={
            "category": "general",
            "description": "The number of alternatives is the number of elements agents had to vote on. It is only "
                           "available for data representing orderings of the alternatives.",
            "is_active": True,
            "is_displayed": True,
            "applies_to": 'soc,soi,toc,toi,tog,mjg,wmg,pwg,wmd',
            "inner_module": "preflibtools.properties",
            "inner_function": "nbAlternatives",
            "inner_type": "int",
            "search_widget": "range",
            "short_name": "numAlt",
            "search_question": "Number of alternatives:",
            "search_res_name": "#Alternatives",
            "order_priority": 1})

    metadata_num_vot, _ = Metadata.objects.update_or_create(
        name="Number of voters",
        defaults={
            "category": "general",
            "description": "The number of voters is the number of ballots that were submitted. For weighted matching "
                           "graphs",
            "is_active": True,
            "is_displayed": True,
            "applies_to": ",".join([t[0] for t in DATATYPES]),
            "inner_module": "preflibtools.properties",
            "inner_function": "nbVoters",
            "inner_type": "int",
            "search_widget": "range",
            "short_name": "numVot",
            "search_question": "Number of voters:",
            "search_res_name": "#Voters",
            "order_priority": 2})

    metadata_sum_vote, _ = Metadata.objects.update_or_create(
        name="Sum of vote count",
        defaults={
            "category": "general",
            "description": """The sum of the weights of the ballots cast. See the data <a 
            href="/data/format#election">format page</a> for more information.""",
            "is_active": True,
            "is_displayed": True,
            "applies_to": ",".join([t[0] for t in DATATYPES]),
            "inner_module": "preflibtools.properties",
            "inner_function": "nbSumVoters",
            "inner_type": "int",
            "search_widget": "range",
            "short_name": "sumVot",
            "search_question": "Sum of vote count:",
            "search_res_name": "Sum Vote Count",
            "order_priority": 3})

    metadata_uniq_orders, _ = Metadata.objects.update_or_create(
        name="Number of unique orders",
        defaults={
            "category": "general",
            "description": "The number of distinct ballots that were casts.",
            "is_active": True,
            "is_displayed": True,
            "applies_to": ",".join([t[0] for t in DATATYPES]),
            "inner_module": "preflibtools.properties",
            "inner_function": "nbDifferentOrders",
            "inner_type": "int",
            "search_widget": "range",
            "short_name": "numUniq",
            "search_question": "Number of unique orders:",
            "search_res_name": "#Unique Ballots",
            "order_priority": 4})

    # metadataNumNodes, _ = Metadata.objects.update_or_create(
    # 	name = "Number of nodes",
    # 	update_or_create(
    #	defaults = {
    #		"category": "general",
    # 		"description": "For data representing graphs, it represents the number of nodes in the graph.",
    # 		"is_active": True,
    #		"is_displayed": True,
    # 		"applies_to": 'tog,mjg,wmg,pwg,wmd',
    # 		"inner_module": "preflibtools.properties",
    # 		"inner_function": "nbAlternatives",
    # 		"inner_type": "int",
    # 		"search_widget": "range",
    # 		"short_name": "numNodes",
    # 		"search_question": "Number of nodes:",
    #		"search_res_name": "",
    #		"order_priority": "")

    metadata_is_strict, _ = Metadata.objects.update_or_create(
        name="Strict orders",
        defaults={
            "category": "preference",
            "description": "A boolean value set to True if all the ballots that were cast represent strict linear "
						   "orders.",
            "is_active": True,
            "is_displayed": False,
            "applies_to": 'soc,soi,toc,toi',
            "inner_module": "preflibtools.properties",
            "inner_function": "isStrict",
            "inner_type": "bool",
            "search_widget": "ternary",
            "short_name": "isStrict",
            "search_question": "Is strict?",
            "search_res_name": "Strict",
            "order_priority": 11})

    metadata_is_complete, _ = Metadata.objects.update_or_create(
        name="Complete orders",
        defaults={
            "category": "preference",
            "description": "A boolean value set to True if all the ballots that were cast represent complete linear "
						   "orders.",
            "is_active": True,
            "is_displayed": False,
            "applies_to": 'soc,soi,toc,toi',
            "inner_module": "preflibtools.properties",
            "inner_function": "isComplete",
            "inner_type": "bool",
            "search_widget": "ternary",
            "short_name": "isComplete",
            "search_question": "Is complete?",
            "search_res_name": "Complete",
            "order_priority": 12})

    metadata_is_app, _ = Metadata.objects.update_or_create(
        name="Approval profile",
        defaults={
            "category": "preference",
            "description": "A boolean value set to True if the ballots can be interpreted as approval ballots. That "
						   "is the case if, either every ballot consist of a single set of indifferences, or every "
						   "ballots is complete and consist of two set of indifferences.",
            "is_active": True,
            "is_displayed": True,
            "applies_to": 'soc,soi,toc,toi',
            "inner_module": "preflibtools.properties",
            "inner_function": "isApproval",
            "inner_type": "bool",
            "search_widget": "ternary",
            "short_name": "isApproval",
            "search_question": "Is an approval profile?",
            "search_res_name": "Approval",
            "order_priority": 13})

    metadata_is_sp, _ = Metadata.objects.update_or_create(
        name="Single-peaked",
        defaults={
            "category": "preference",
            "description": """A boolean value set to True if the set of ballots cast represents <a 
            href="https://en.wikipedia.org/wiki/Single_peaked_preferences">single-peaked preferences</a>. To check 
            this property, we used the <a href="https://github.com/zmf6921/incompletesp">code of Zack Fitzsimmons and 
            Martin Lackner</a> available on GitHub that we want to thank here.""",
            "is_active": True,
            "is_displayed": True,
            "applies_to": 'soc',
            "inner_module": "preflibtools.properties",
            "inner_function": "isSP",
            "inner_type": "bool",
            "search_widget": "ternary",
            "short_name": "isSP",
            "search_question": "Is single-peaked?",
            "search_res_name": "Single-Peaked",
            "order_priority": 14})

    metadata_is_sc, _ = Metadata.objects.update_or_create(
        name="Single-crossing",
        defaults={
            "category": "preference",
            "description": "A boolean value set to True if the set of ballots cast represents single-crossing "
						   "preferences.",
            "is_active": True,
            "is_displayed": True,
            "applies_to": 'soc',
            "inner_module": "preflibtools.properties",
            "inner_function": "isSC",
            "inner_type": "bool",
            "search_widget": "ternary",
            "short_name": "isSC",
            "search_question": "Is single-crossing?",
            "search_res_name": "Single-Crossing",
            "order_priority": 15})

    metadata_larg_ballot, _ = Metadata.objects.update_or_create(
        name="Size of the largest ballot",
        defaults={
            "category": "ballot",
            "description": """Given a set of ballots, how many alternatives have been submitted in the ballot with 
            the highest number of submitted alternatives. In data representing complete orders (<a 
            href="/data/types#soc">SOC</a> and <a href="/data/types#toc">TOC</a>), this should be equal to the number 
            of alternatives.""",
            "is_active": True,
            "is_displayed": True,
            "applies_to": 'soc,soi,toc,toi',
            "inner_module": "preflibtools.properties",
            "inner_function": "largestBallot",
            "inner_type": "int",
            "search_widget": "range",
            "short_name": "largestBallot",
            "search_question": "Size of the largest ballot:",
            "search_res_name": "Largest Ballot",
            "order_priority": 6})

    metadata_smal_ballot, _ = Metadata.objects.update_or_create(
        name="Size of the smallest ballot",
        defaults={
            "category": "ballot",
            "description": """Given a set of ballots, how many alternatives have been submitted in the ballot with 
            the smallest number of submitted alternatives. In data representing complete orders (<a 
            href="/data/types#soc">SOC</a> and <a href="/data/types#toc">TOC</a>), this should be equal to the number 
            of alternatives.""",
            "is_active": True,
            "is_displayed": True,
            "applies_to": 'soc,soi,toc,toi',
            "inner_module": "preflibtools.properties",
            "inner_function": "smallestBallot",
            "inner_type": "int",
            "search_widget": "range",
            "short_name": "smallestBallot",
            "search_question": "Size of the smallest ballot:",
            "search_res_name": "Smallest Ballot",
            "order_priority": 5})

    metadata_max_num_indif, _ = Metadata.objects.update_or_create(
        name="Maximum number of indifferences",
        defaults={
            "category": "ballot",
            "description": """In a given ballot, an indifference is a position in the order such that more than one 
            alternative is ranked at this position. Given a set of ballots, the maximum number of indifferences is 
            the number of indifferences in the ballot with the highest number of them. In data witout ties (<a 
            href="/data/types#soc">SOC</a> and <a href="/data/types#soi">SOI</a>), this should be 0.""",
            "is_active": True,
            "is_displayed": True,
            "applies_to": 'soc,soi,toc,toi',
            "inner_module": "preflibtools.properties",
            "inner_function": "maxNbIndif",
            "inner_type": "int",
            "search_widget": "range",
            "short_name": "maxNumIndif",
            "search_question": "Maximum number of indifferences:",
            "search_res_name": "Max #Indif.",
            "order_priority": 8})

    metadata_min_num_indif, _ = Metadata.objects.update_or_create(
        name="Minimum number of indifferences",
        defaults={
            "category": "ballot",
            "description": """In a given ballot, an indifference is a position in the order such that more than one 
            alternative is ranked at this position. Given a set of ballots, the minimum number of indifferences is 
            the number of indifferences in the ballot with the smallest number of them. In data witout ties (<a 
            href="/data/types#soc">SOC</a> and <a href="/data/types#soi">SOI</a>), this should be 0.""",
            "is_active": True,
            "is_displayed": True,
            "applies_to": 'soc,soi,toc,toi',
            "inner_module": "preflibtools.properties",
            "inner_function": "minNbIndif",
            "inner_type": "int",
            "search_widget": "range",
            "short_name": "minNumIndif",
            "search_question": "Minimum number of indifferences:",
            "search_res_name": "Min #Indif.",
            "order_priority": 7})

    metadata_larg_indif, _ = Metadata.objects.update_or_create(
        name="Size of the largest indifference",
        defaults={
            "category": "ballot",
            "description": """In a given ballot, an indifference is a position in the order such that more than one 
            alternative is ranked at this position. Given a set of ballots, the size of the largest indifference is 
            the maximal number of alternatives which are tied in a ballot. In data witout ties (<a 
            href="/data/types#soc">SOC</a> and <a href="/data/types#soi">SOI</a>), this should be 0.""",
            "is_active": True,
            "is_displayed": True,
            "applies_to": 'soc,soi,toc,toi',
            "inner_module": "preflibtools.properties",
            "inner_function": "largestIndif",
            "inner_type": "int",
            "search_widget": "range",
            "short_name": "largestIndif",
            "search_question": "Size of the largest indifference:",
            "search_res_name": "Largest Indif.",
            "order_priority": 10})

    metadata_smal_indif, _ = Metadata.objects.update_or_create(
        name="Size of the smallest indifference",
        defaults={
            "category": "ballot",
            "description": """In a given ballot, an indifference is a position in the order such that more than one 
            alternative is ranked at this position. Given a set of ballots, the size of the largest indifference is 
            the maximal number of alternatives which are tied in a ballot. In data witout ties (<a 
            href="/data/types#soc">SOC</a> and <a href="/data/types#soi">SOI</a>), this should be 0.""",
            "is_active": True,
            "is_displayed": True,
            "applies_to": 'soc,soi,toc,toi',
            "inner_module": "preflibtools.properties",
            "inner_function": "smallestIndif",
            "inner_type": "int",
            "search_widget": "range",
            "short_name": "smallestIndif",
            "search_question": "Size of the smallest indifference:",
            "search_res_name": "Smallest Indif.",
            "order_priority": 9})

    # metadataObj, _ = Metadata.objects.update_or_create(
    # 	name = "Condorcet winner",
    # 	update_or_create(
    #	defaults = {
    #		"category": "graph",
    # 		"description": """A boolean value set to True if the ballot represented as a graph admits a <a href="https://en.wikipedia.org/wiki/Condorcet_criterion">Condorcet winner</a>.""",
    # 		"is_active": True,
    #		"is_displayed": True,
    # 		"applies_to": 'tog,mjg,wmg,pwg',
    # 		"inner_module": "preflibtools.properties",
    # 		"inner_function": "hasCondorcet",
    # 		"inner_type": "bool",
    # 		"search_widget": "ternary",
    # 		"short_name": "hasCondorcet",
    # 		"search_question": "Has a Condorcet winner?",
    #		"search_res_name": "",
    #		"order_priority": "")

    metadata_num_alt.upper_bounds.set([])
    metadata_num_alt.upper_bounds.add(metadata_smal_ballot)
    metadata_num_alt.upper_bounds.add(metadata_larg_ballot)
    metadata_num_alt.upper_bounds.add(metadata_smal_indif)
    metadata_num_alt.upper_bounds.add(metadata_larg_indif)


class Command(BaseCommand):
    help = "Initializes the database, to be run once at the beginning"

    def handle(self, *args, **options):
        initialize_tags()
        initialize_metadata()
