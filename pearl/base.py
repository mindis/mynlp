import abc

class Policy(object, metaclass=abc.ABCMeta):
    """
    General policy interface.
    """
    @abc.abstractmethod
    def get_action(self, observation):
        """
        :param observation:
        :return: action, debug_dictionary
        """
        pass

    def reset(self):
        pass

