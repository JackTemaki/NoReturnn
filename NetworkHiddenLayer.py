
from theano import tensor as T
from NetworkBaseLayer import Layer
from ActivationFunctions import strtoact


class HiddenLayer(Layer):
  recurrent = False

  def __init__(self, activation="tanh", **kwargs):
    """
    :type activation: str | list[str]
    """
    kwargs.setdefault("layer_class", "hidden")
    super(HiddenLayer, self).__init__(**kwargs)
    self.set_attr('activation', activation.encode("utf8"))
    self.activation = strtoact(activation)
    self.W_in = [self.add_param(self.create_forward_weights(s.attrs['n_out'],
                                                            self.attrs['n_out'],
                                                            name="W_in_%s_%s" % (s.name, self.name)))
                 for s in self.sources]
    self.set_attr('from', ",".join([s.name for s in self.sources]))


class ForwardLayer(HiddenLayer):
  def __init__(self, **kwargs):
    kwargs.setdefault("layer_class", "hidden")
    super(ForwardLayer, self).__init__(**kwargs)
    z = self.b
    assert len(self.sources) == len(self.masks) == len(self.W_in)
    for s, m, W_in in zip(self.sources, self.masks, self.W_in):
      if s.attrs['sparse']:
        z += W_in[T.cast(s.output[:,:,0], 'int32')]
      elif m is None:
        z += self.dot(s.output, W_in)
      else:
        z += self.dot(self.mass * m * s.output, W_in)
    self.make_output(z if self.activation is None else self.activation(z))


class StateToAct(ForwardLayer):
  def __init__(self, **kwargs):
    kwargs['n_out'] = 1
    kwargs.setdefault("layer_class", "state_to_act")
    super(StateToAct, self).__init__(**kwargs)
    self.make_output(T.concatenate([s.act[-1][-1] for s in self.sources], axis=-1).dimshuffle('x',0,1).repeat(self.sources[0].output.shape[0], axis = 0))
    self.attrs['n_out'] = sum([s.attrs['n_out'] for s in self.sources])


class ConvPoolLayer(ForwardLayer):
  def __init__(self, **kwargs):
    kwargs.setdefault("layer_class", "convpool")
    super(ConvPoolLayer, self).__init__(**kwargs)
