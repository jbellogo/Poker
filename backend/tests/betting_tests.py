import pytest
from models import *
from unittest.mock import AsyncMock
import pprint
import asyncio
import pytest_asyncio


@pytest.mark.asyncio
async def test_player_make_bet(monkeypatch, player_list_fix, game_state_preflop_fix):
    
    actions = [
        {
            'sid' : player.sid,
            'amount_bet' : 40,
            'action' : "call"
        } for player in player_list_fix]    
    
    test_mock = AsyncMock(side_effect=actions)
    monkeypatch.setattr(Player, "request_betting_response", test_mock)

    for i, player in enumerate(player_list_fix):
        old_funds = player.funds
        response = await player.make_bet(game_state_preflop_fix)
        assert response == actions[i]
        assert player.current_bet == actions[i]['amount_bet']
        assert old_funds - player.funds == actions[i]['amount_bet']
        assert player.betting_status == PlayerAction(actions[i]['action']).to_status()

########################################################
#### PREFLOP TESTS
########################################################

@pytest.mark.asyncio
async def test_betting_round_1(monkeypatch, game_fix):
    '''
    Situation: All players call the big blind
    game_fix num_players=3 and sb_amount=20
    '''
    assert [player.get_id() for player in game_fix.players] == [1,2,3]

    actions = [
        {'sid' : '3', 'amount_bet' : 40, 'action' : "call"},
        {'sid' : '1', 'amount_bet' : 20, 'action' : "call"},
        {'sid' : '2', 'amount_bet' : 0, 'action' : "check"},
    ]
    test_mock = AsyncMock(side_effect=actions)
    monkeypatch.setattr(Player, "request_betting_response", test_mock)
    await game_fix.betting_round(board_stage="PREFLOP")   ## @TODO I'm thinking we will need asyncio.gather()
    hand_history = game_fix.get_hand_history()['PREFLOP']
    assert(len(hand_history)==3) # only three bets all call.

    assert(hand_history[0]['game_state']['pot'] == {'call_total' : 40,'check_allowed' : False,'minimum_raise' : 80,'pot_size' : 60})
    assert(hand_history[1]['game_state']['pot'] == {'call_total' : 40,'check_allowed' : False,'minimum_raise' : 80,'pot_size' : 100})
    assert(hand_history[2]['game_state']['pot'] == {'call_total' : 40,'check_allowed' : True,'minimum_raise' : 80,'pot_size' : 120})
    
    assert(hand_history[0]['response'] == {'action': 'call','amount_bet': 40,'sid': '3'})
    assert(hand_history[1]['response'] == {'action': 'call','amount_bet': 20,'sid': '1'})
    assert(hand_history[2]['response'] == {'action': 'check','amount_bet': 0,'sid': '2'})


@pytest.mark.asyncio
async def test_betting_round_2(monkeypatch, game_fix):
    '''
    Preflop stage
    history: P1 is sb pays 20, P2 is bb pays 40, P3 is other starts action
    Situation: single raise 
    '''
    # Situation:
    actions = [
        {'sid' : '3', 'amount_bet' : 40, 'action' : "call"},
        {'sid' : '1', 'amount_bet' : 80, 'action' : "raise"}, # P1 total 100
        {'sid' : '2', 'amount_bet' : 60, 'action' : "call"}, # P2 total 100
        {'sid' : '3', 'amount_bet' : 60, 'action' : "call"} # P3 total 100
    ]

    test_mock = AsyncMock(side_effect=actions)
    monkeypatch.setattr(Player, "request_betting_response", test_mock)
    await game_fix.betting_round(board_stage="PREFLOP")
    hand_history = game_fix.get_hand_history()['PREFLOP']

    pprint.pp(hand_history)
    assert(len(hand_history)==4)
    # P3 saw this bellow and called 40
    assert(hand_history[0]['game_state']['pot'] == {"call_total" : 40, "call_total" : 40,"check_allowed" : False,"minimum_raise" : 80,"pot_size" : 0})
    assert(hand_history[0]['player_state']['public_info']['pid'] == 3)
    assert(hand_history[0]['player_state']['public_info']['role'] == 'other')
    assert(hand_history[0]['player_state']['public_info']['funds'] == 960)
    assert(hand_history[0]['player_state']['last_action'] == 'call')
    assert(hand_history[0]['player_state']['current_bet'] == 40)

    # P1 saw this bellow and raised 80
    assert(hand_history[1]['game_state']['pot'] == {"call_total" : 40,"check_allowed" : False,"minimum_raise" : 80,"pot_size" : 40})
    assert(hand_history[1]['player_state']['public_info']['pid'] == 1)
    assert(hand_history[1]['player_state']['public_info']['role'] == 'sb')
    assert(hand_history[1]['player_state']['public_info']['funds'] == 900)
    assert(hand_history[1]['player_state']['last_action'] == 'raise')
    assert(hand_history[1]['player_state']['current_bet'] == 80)
    
    # P2 saw this bellow and called 80
    assert(hand_history[2]['game_state']['pot'] == {"call_total" : 80,"check_allowed" : False,"minimum_raise" : 160,"pot_size" : 120})
    # P3 calls his remainding 40
    assert(hand_history[3]['game_state']['pot'] == {"call_total" : 80,"check_allowed" : False,"minimum_raise" : 160,"pot_size" : 200})


# @pytest.mark.asyncio
# async def test_betting_round3(monkeypatch, game_fix):
#     '''
#     Situation: flop stage, check allowed, multiple raises. 
#     '''
#     actions_preflop = [('P1','call', 40), ('P2','raise',80), ('P3','call', 80), ('P1','call', 40), ('P2','check',0), ('P3','check', 0)]
#     actions_flop = [('P1','check', 0), ('P2','raise',100), ('P3','raise', 200), ('P1','call', 200), ('P2','call', 100), ('P3','check', 0)]
#     test_mock = AsyncMock(side_effect=get_player_actions(actions_preflop+actions_flop))
#     monkeypatch.setattr(Player, "request_betting_response", test_mock)

#     # Preflop
#     await game_fix.betting_round(board_stage=BoardStage.PREFLOP)
#     # FLOP actions:
#     flop_initial_conditions = {
#       "call_total" : 0,
#       "check_allowed" : True,
#       "minimum_raise" : 80,
#       "pot_size" : 240,
#     }

#     # test_mock = AsyncMock(side_effect=get_player_actions(actions))
#     # monkeypatch.setattr(Player, "request_betting_response", test_mock) # NEW mocked method!!!!!
#     await game_fix.betting_round(BoardStage.FLOP)
#     hand_history = game_fix.get_hand_history()['FLOP']

#     assert(len(hand_history)==6) # 5 moves total... gotta wait for EVERYONE
#     # P1 sees this bellow and checks
#     assert(hand_history[0]['game_state']['pot'] == flop_initial_conditions)
#     # P2 sees this bellow and raises 100
#     assert(hand_history[1]['game_state']['pot'] == flop_initial_conditions)
#     ## P3 sees this bellow and raises 200
#     assert(hand_history[2]['game_state']['pot'] == {'call_total': 100,'check_allowed' : False,'minimum_raise' : 200,'pot_size' : 340})
#     ## P1 sees this bellow and calls 200
#     assert(hand_history[3]['game_state']['pot'] == {"call_total" : 200,"check_allowed" : False,"minimum_raise" : 400,"pot_size" : 540})
#     ## P2 Calls with 100
#     assert(hand_history[4]['game_state']['pot'] == {"call_total" : 100,   "check_allowed" : False,"minimum_raise" : 400,"pot_size" : 740})

    
# @pytest.mark.asyncio
# async def test_betting_round4(monkeypatch, game_fix):
#     '''
#     Situation: pre-flop stage, player folds. 
#     '''
#     # PREFLOP actions:
#     actions = [('P1','call',40), ('P2','raise',80), ('P3','fold',0), ('P1','raise',160), ('P2','call',120)] # P3 actually not allowed to check   
#     # with fold and call you should not have to specify, maybe we can worry about that in the frontend
#     test_mock = AsyncMock(side_effect=get_player_actions(actions))
#     monkeypatch.setattr(Player, "request_betting_response", test_mock)
#     await game_fix.betting_round(board_stage=BoardStage.PREFLOP)
    
#     hand_history = game_fix.get_hand_history()['PREFLOP']

#     assert(len(hand_history)==5)

#     assert(hand_history[0]['game_state']['pot']=={'call_total' : 40,'check_allowed' : False,'minimum_raise' : 80,'pot_size' : 0}) # P1 sees
#     assert(hand_history[1]['game_state']['pot']=={'call_total' : 40,'check_allowed' : False,'minimum_raise' : 80,'pot_size' : 40}) # P2 sees
#     assert(hand_history[2]['game_state']['pot']=={'call_total' : 80,'check_allowed' : False,'minimum_raise' : 160,'pot_size' : 120}) # P3 sees
#     assert(hand_history[3]['game_state']['pot']=={'call_total' : 40,'check_allowed' : False,'minimum_raise' : 160,'pot_size' : 120}) # P1 sees
#     assert(hand_history[4]['game_state']['pot']=={'call_total' : 120,'check_allowed' : False,'minimum_raise' : 320,'pot_size' : 280}) # P2 sees


# # # @TODO test validation of call amounts and minimum raises. 
# # # Test blind taxes in preflop round, they should not be able to fold
# # # Test all-in 

# @pytest.mark.asyncio
# async def test_betting_round_5(monkeypatch, game_fix):
#     '''
#     Situation: pre-flop stage, player goes all-in. 
#     '''
#     actions = [('P1','call',40), ('P2','call',40), ('P3','all-in',5000), ('P1','fold',0), ('P2','all-in',4960)] # P3 actually not allowed to check   
#     # with fold and call you should not have to specify, maybe we can worry about that in the frontend
#     test_mock = AsyncMock(side_effect=get_player_actions(actions))
#     monkeypatch.setattr(Player, "request_betting_response", test_mock)
#     await game_fix.betting_round(board_stage=BoardStage.PREFLOP)
#     hand_history = game_fix.get_hand_history()['PREFLOP']
#     pprint.pprint(hand_history)
#     assert(len(hand_history)==5)









