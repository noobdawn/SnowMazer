from Actions.BaseAction import Condition, BaseAction

class ITVCondition(Condition):
    # 操作执行的条件
    CONDITIONS_RIGHT_DISTANCE_BIGGER_THAN = 101
    CONDITIONS_LEFT_DISTANCE_BIGGER_THAN = 102
    CONDITIONS_UP_DISTANCE_BIGGER_THAN = 103
    CONDITIONS_DOWN_DISTANCE_BIGGER_THAN = 104
    CONDITIONS_RIGHT_DISTANCE_BELOW = 105
    CONDITIONS_LEFT_DISTANCE_BELOW = 106
    CONDITIONS_UP_DISTANCE_BELOW = 107
    CONDITIONS_DOWN_DISTANCE_BELOW = 108

class ITVAction(BaseAction):
    def __init__(self,
                    startAction : int, startActionParams : dict,
                    endCondition : int, endConditionParams : dict,
                    endAction : int, endActionParams : dict,
                    hint : str):
        super().__init__(startAction, startActionParams, endCondition, endConditionParams, endAction, endActionParams, hint)
        self.__conditionMetTime = 3


    def setDistance(self, rightDistance, leftDistance, upDistance, downDistance):
        self.endConditionParams['rightDistance'] = rightDistance
        self.endConditionParams['leftDistance'] = leftDistance
        self.endConditionParams['upDistance'] = upDistance
        self.endConditionParams['downDistance'] = downDistance


    def _isConditionMet(self) -> bool:        
        if self.endCondition == ITVCondition.CONDITIONS_RIGHT_DISTANCE_BIGGER_THAN:
            result = self.endConditionParams['rightDistance'] > self.endConditionParams['rightDistanceLimit']
        elif self.endCondition == ITVCondition.CONDITIONS_LEFT_DISTANCE_BIGGER_THAN:
            result = self.endConditionParams['leftDistance'] > self.endConditionParams['leftDistanceLimit']
        elif self.endCondition == ITVCondition.CONDITIONS_UP_DISTANCE_BIGGER_THAN:
            result = self.endConditionParams['upDistance'] > self.endConditionParams['upDistanceLimit']
        elif self.endCondition == ITVCondition.CONDITIONS_DOWN_DISTANCE_BIGGER_THAN:
            result = self.endConditionParams['downDistance'] > self.endConditionParams['downDistanceLimit']
        elif self.endCondition == ITVCondition.CONDITIONS_RIGHT_DISTANCE_BELOW:
            result = self.endConditionParams['rightDistance'] < self.endConditionParams['rightDistanceLimit']
        elif self.endCondition == ITVCondition.CONDITIONS_LEFT_DISTANCE_BELOW:
            result = self.endConditionParams['leftDistance'] < self.endConditionParams['leftDistanceLimit']
        elif self.endCondition == ITVCondition.CONDITIONS_UP_DISTANCE_BELOW:
            result = self.endConditionParams['upDistance'] < self.endConditionParams['upDistanceLimit']
        elif self.endCondition == ITVCondition.CONDITIONS_DOWN_DISTANCE_BELOW:
            result = self.endConditionParams['downDistance'] < self.endConditionParams['downDistanceLimit']
        else:
            return super()._isConditionMet()
        # 必须连续3次满足条件才算
        if result:
            self.__conditionMetTime -= 1
            if self.__conditionMetTime <= 0:
                return True
        else:
            self.__conditionMetTime = 3
        return False
    

MAKE_RIGHT_DICT = lambda rightDistanceLimit : {'rightDistanceLimit': rightDistanceLimit}
MAKE_LEFT_DICT = lambda leftDistanceLimit : {'leftDistanceLimit': leftDistanceLimit}
MAKE_UP_DICT = lambda upDistanceLimit : {'upDistanceLimit': upDistanceLimit}
MAKE_DOWN_DICT = lambda downDistanceLimit : {'downDistanceLimit': downDistanceLimit}