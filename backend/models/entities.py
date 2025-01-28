'''
Card entities are Card object owners: Deck, Board, and Players.
'''

from pydantic import BaseModel
from models.definitions import *
from typing import List, Union, Literal, Tuple, Optional
import random
from enum import IntEnum
from uuid import UUID
from abc import ABC, abstractmethod
import asyncio
from aiohttp import ClientSession

###  
### Entities are Card owners.

class Entity(BaseModel, ABC):
    '''A Card Owner'''
    cards : List[Card] = []

    def add_card(self, card : Card) -> None:
        self.cards.append(card)

    def length(self):
        return len(self.cards)
    
    def has(self, card: Card) -> bool:
        return card in self.cards      
    
    def __str__(self) -> str:
        return self.cards
    
    @abstractmethod
    def _cards_dealt(self) -> int:
        pass


class Player(Entity):
    pid : int
    sid : str
    funds : int
    number_cards_dealt : int = 2
    role : PlayerRole = PlayerRole.OTHER  # @TODO update them every round
    betting_status : PlayerStatus = PlayerStatus.INACTIVE

    hand : Tuple[Card, Card] = None
    amount_bet_this_hand : int = 0

    def __str__(self):
        return self.model_dump_json()

    def _cards_dealt(self) -> int:
        return self.number_cards_dealt
    
    def get_betting_status(self):
        return self.betting_status
    
    def set_role(self, role: PlayerRole)->None:
        self.role = role
    
    def get_id(self) -> int:
        return self.pid

    def set_status(self, new_status : Literal["active", "fold", "all-in", "inactive"]):
        self.betting_status = new_status
    
    def f_amount_bet_this_hand(self):
        return self.amount_bet_this_hand
    
    def reset_amount_bet_this_hand(self):
        self.amount_bet_this_hand = 0
    
    # def add_amount_bet_this_hand(self, amount:int):
    #     ''' this is only used for testing'''
    #     self.current_hand_amount_bet+=amount


    async def request_betting_response(self) -> Optional[PlayerBetResponse]:
        '''Actual API call'''
        await asyncio.sleep(1)
        return None


    async def make_bet(self, game_state: GameState) -> Optional[PlayerBetResponse]: 
        '''
        pot_state : PotState argument neeed
        @TODO NEEDS VALIDATORS of call amounts, minimum raises, blinds in preflop round, etc. 
        Wrapper that Uses API response from request_betting_response() and updates local player fields.
        '''
        ### prepare the JSON information package to send to player to make a betting decision: 

        
        # @TODO Implement API to connect to frontend. 
        ## 1**) send request to player's ip address, await resposne.
        ## this should already be validated as the pre_bet_state is betting constraints served to player. Cannot bet more than funds!
        response : PlayerBetResponse  = await self.request_betting_response() # pass to it a GameState and PlayerState
        print(f"bet:{response['amount_bet']}, funds: {self.funds}")
        assert(response['amount_bet'] <= self.funds)
        # We want to keep the game logic on the backend, so we can determine the options avaliable here and send them to the frontend.
        if(response['action'] == 'fold') or (response['action'] == 'check'):
            assert(response['amount_bet']==0) 
        if(response['action'] == 'all-in'):
            assert(response['amount_bet']==self.funds)
        if(response['action'] == 'call'):
            assert(response['amount_bet']==game_state['pot']['call_amount'])            
        # response = PlayerBetResponse({
        #     "pid": self.pid,
        #     "player_funds" : self.funds,
        #     "amount_bet" : 55,
        #     "role": self.role,
        #     "action" : "Fold", 
        #     "hand" : self.hand,
        # })

        # Handle 

        # update local player records with response. 
        self.funds -= response['amount_bet']
        self.betting_status = PlayerAction(response['action']).to_status()  ## this one is iffy
        self.amount_bet_this_hand += response['amount_bet']

        return response


###########



class Board(Entity):
    '''
    shows the community cards. 
    '''
    stage : BoardStage = BoardStage.PREFLOP

    def __str__(self) -> str:
        return super().__str__()
    
    # def current_stage(self) -> BoardStage:
    #     return self.stage

    # def next_stage(self) -> bool:
    #     indicator = self.stage < BoardStage.RIVER
    #     if indicator:
    #         self.stage +=1
        
    #     return indicator
    def set_round(self, stage : BoardStage):
        self.stage = stage.value

    def best_hand(self, player_hand : List[Card]):
        pass

    def show(self)->None:
        print(self.cards) ## for now. 

    def get_state(self) -> BoardState:
        return BoardState(stage=self.stage, cards =self.cards)

    def _cards_dealt(self) -> int:
        '''Number of cards dealt. 3 on FLOP, 1 On turn, 1 on river.'''
        if self.stage == BoardStage.PREFLOP:
            return 3
        if self.stage > BoardStage.PREFLOP:
            return 1
        return 0

class Deck(Entity):
    def __init__(self):
        super().__init__()
        self.initialize_deck()
        self.shuffle()

    def initialize_deck(self):
        for suit in Suit.list():
            for rank in Rank.list():
                card = Card(suit=suit, rank=rank)
                self.add_card(card)

    def shuffle(self):
        random.shuffle(self.cards)
        random.shuffle(self.cards)

    
    def deal_cards(self, entity : Entity) -> List[Card]:
        '''
        Removes card from deck and deals it to entity according to enty type.
        Removed cards returned for testing
        '''
        cards = []
        for i in range(0, entity._cards_dealt()):
            card = self.cards.pop()
            entity.add_card(card)    
            cards.append(card)   
        return cards
    
    def _cards_dealt(self) -> int:
        return 0
    


        




