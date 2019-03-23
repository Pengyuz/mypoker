from pypokerengine.players import BasePokerPlayer

import random as rand

import pprint

class TestPlayer(BasePokerPlayer):

    def __init__(self):
        self.my_stack = 1000
   
    def build_game_state(self, valid_actions, hole_card, round_state):

        game_state = {}

        game_state["turn"] = "me"
        game_state["street"] = round_state["street"]
        game_state["community_card"] = round_state["community_card"]
        game_state["my_hole_card"] = hole_card
       
        pot = round_state["pot"]["main"]["amount"]
        game_state["pot"] = pot
       
        b = 0
        player_uuids_stacks = [(player_info['uuid'], player_info["stack"]) for player_info in round_state["seats"]]
        for (uuid, stack) in player_uuids_stacks:

            if uuid == self.uuid:

                b = self.my_stack - stack
       
        game_state["my_bet"] = b
        game_state["oppo_bet"] = pot - b
        game_state["valid_actions"] = valid_actions
        return game_state
   
    def expectiminimax(self, node):
        MAX_INT = 1e20
        if node.is_terminal():
            return node.value
        if node.type == 'self':
            q = -MAX_INT
            for child in node.children:
                q = max(q, self.expectiminimax(child))
        elif node.type == 'oppo':
            q_list = []
            proba_ditri = [0.33, 0.33, 0.33] # oppo model
            for child in node.children:
                q_list.append(self.expectiminimax(child))
            q = sum([i*j for i,j in zip(q_list, proba_ditri)])
        elif node.type == 'nature':
            q = 0
            for child in node.children:
                # All children are equally probable
                q += len(node.children)**-1 * self.expectiminimax(child)
        elif node.type == 'fold':
            return node.value
        node.set_value(q)
        return q
   
    def add_nature_node_children(self, nature_node, depth):
        '''
        append chldren of this nature_node
        '''
        old_game_state = nature_node.game_state
        new_game_state = old_game_state
       
       # simulate new_game_state, append all to nature_node
       #for i in range(n):
        if old_game_state["street"] == "preflop":
            new_game_state["street"] = "flop"
            new_game_state["community_card"] = [] # add 3
        elif old_game_state["street"] == "flop":
            new_game_state["street"] = "turn"
            new_game_state["community_card"] = [] # add 1
        elif old_game_state["street"] == "turn":
            new_game_state["street"] = "river"
            new_game_state["community_card"] = [] # add 1
        elif old_game_state["street"] == "river":
            new_game_state["street"] = "showdown"
            new_game_state["community_card"] = []
       
        nature_node.add_child(self.construct_tree(new_game_state, depth+1))
   
    def evaluate(self, game_state):
        '''
        evaluation function for cut off nodes
        '''
        return 0

    def construct_tree(self, game_state, depth):
       
        if game_state["turn"] == "me":
           
            node = TreeNode([], 0, "self", game_state)
            if depth == 10:
                node.set_value(self.evaluate(game_state))
                return node

            my_bet = game_state["my_bet"]
            oppo_bet = game_state["oppo_bet"]
            for action in game_state["valid_actions"]:

                if action["action"] == "fold":

                    node.add_child(TreeNode([], -game_state["my_bet"], "fold", None))

                elif action["action"] == "raise":

                    new_game_state = game_state
                    new_game_state["turn"] = "oppo"
                    new_game_state["pot"] = new_game_state["pot"] + oppo_bet+10-my_bet
                    new_game_state["my_bet"] = new_game_state["my_bet"] + oppo_bet+10-my_bet
                    
                    #if raise_time == 4
                    new_valid_actions = [{ "action" : "fold"  },{ "action" : "call" },{ "action" : "raise" }]
                    
                    new_game_state["valid_actions"] = new_valid_actions
                    node.add_child(self.construct_tree(new_game_state, depth+1))
               
                elif action["action"] == "call":
                   
                    if my_bet == oppo_bet:
                        nature_node = TreeNode([], 0, "nature", game_state)
                        node.add_child(nature_node)
                        self.add_nature_node_children(nature_node, depth)
                    else:
                        new_game_state = game_state
                        new_game_state["turn"] = "oppo"
                        new_game_state["pot"] = new_game_state["pot"] + 10
                        new_game_state["my_bet"] = new_game_state["my_bet"] + 10

                        #if raise_time == 4
                        new_valid_actions = [{ "action" : "fold"  },{ "action" : "call" },{ "action" : "raise" }]
                        new_game_state["valid_actions"] = new_valid_actions
                        node.add_child(self.construct_tree(new_game_state, depth+1))
               
            return node
       
        else:
            node = TreeNode([], 0, "oppo", game_state)
            if depth == 10:
                node.set_value(self.evaluate(game_state))
                return node
           
            my_bet = game_state["my_bet"]
            oppo_bet = game_state["oppo_bet"]
            for action in game_state["valid_actions"]:

                if action["action"] == "fold":

                    node.add_child(TreeNode([], game_state["oppo_bet"], "fold", None))

                elif action["action"] == "raise":

                    new_game_state = game_state
                    new_game_state["turn"] = "me"
                    new_game_state["pot"] = new_game_state["pot"] + my_bet+10-oppo_bet
                    new_game_state["oppo_bet"] = new_game_state["oppo_bet"] + my_bet+10-oppo_bet

                    #if raise_time == 4
                    new_valid_actions = [{ "action" : "fold"  },{ "action" : "call" },{ "action" : "raise" }]
                    new_game_state["valid_actions"] = new_valid_actions
                    node.add_child(self.construct_tree(new_game_state, depth+1))
               
                elif action["action"] == "call":
                   
                    if my_bet == oppo_bet:
                        nature_node = TreeNode([], 0, "nature", game_state)
                        node.add_child(nature_node)
                        self.add_nature_node_children(nature_node, depth)
                    else:
                        new_game_state = game_state
                        new_game_state["turn"] = "me"
                        new_game_state["pot"] = new_game_state["pot"] + 10
                        new_game_state["oppo_bet"] = new_game_state["oppo_bet"] + 10

                        #if raise_time == 4
                        new_valid_actions = [{ "action" : "fold"  },{ "action" : "call" },{ "action" : "raise" }]
                        new_game_state["valid_actions"] = new_valid_actions
                        node.add_child(self.construct_tree(new_game_state, depth+1))
               
            return node
   
    #  we define the logic to make an action through this method. (so this method would be the core of your AI)
    def declare_action(self, valid_actions, hole_card, round_state):
        
        game_state = self.build_game_state(valid_actions, hole_card, round_state)
        pp = pprint.PrettyPrinter(indent=2)
        #print("------------ROUND_STATE(testpalyer)--------")
        #pp.pprint(round_state)
        print("------------GAME_STATE(testpalyer)--------")
        pp.pprint(game_state)
        #print("my stack:" + str(self.my_stack))
        
        start_node = self.construct_tree(game_state, 1)
        self.expectiminimax(start_node)
        res = []
        for child in start_node.children:
            res.append(child.value)
        index = res.index(max(res))
        action = valid_actions[index]["action"]
        return action
        

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        player_uuids_stacks = [(player_info['uuid'], player_info["stack"]) for player_info in round_state["seats"]]
        for (uuid, stack) in player_uuids_stacks:
            
            if uuid == self.uuid:
                
                self.my_stack = stack
   
class TreeNode(object):
    def __init__(self, children=None, value=None, type=None, game_state=None):
        self.children = []
        self.value = value
        self.type = type  # either 'self', 'oppo', 'nature' or 'fold'
        self.game_state = game_state
        if children is not None:
            for child in children:
                self.add_child(child)

    def add_child(self, node):
        self.children.append(node)

    def is_terminal(self):
        return len(self.children) == 0
   
    def set_value(self, value):
        self.value = value
