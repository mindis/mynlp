
import numpy as np
import tensorflow as tf


class Distribution(object):
    @property
    def dim(self):
        raise NotImplementedError

    def kl_sym(self, old_dist_info_vars, new_dist_info_vars):
        raise NotImplementedError

    def kl(self, old_dist_info, new_dist_info):
        raise NotImplementedError

    def likelihood_ratio_sym(self, x_var, old_dist_info_vars, new_dist_info_vars):
        raise NotImplementedError

    def entropy(self, dist_info):
        raise NotImplementedError

    def log_likelihood_sym(self, x_var, dist_info_vars):
        raise NotImplementedError

    def log_likelihood(self, xs, dist_info):
        raise NotImplementedError

    @property
    def dist_info_specs(self):
        raise NotImplementedError

    @property
    def dist_info_keys(self):
        return [k for k, _ in self.dist_info_specs]


class DiagonalGaussian(Distribution):
    def __init__(self, dim):
        self._dim = dim

    @property
    def dim(self):
        return self._dim

    def kl(self, old_dist_info, new_dist_info):
        old_means = old_dist_info['mean']
        old_log_stds = old_dist_info['log_std']

        new_means = new_dist_info['mean']
        new_log_stds = new_dist_info['log_std']

        old_std = np.exp(old_log_stds)
        new_std = np.exp(new_log_stds)
        # means: N * A
        # stds: N * A
        # formula: {(mu1 - mu2)^2 + sig1^2 - sig2^2} / (2*sig2^2) + ln(sig2 / sig1)
        numerator = np.square(old_means - new_means) + np.square(old_std) - np.square(new_std)
        denominator = 2 * np.square(new_std) + 1e-8

        return np.sum(numerator / denominator + new_log_stds - old_log_stds, axis=-1)

    def kl_sym(self, old_dist_info_vars, new_dist_info_vars):
        old_means = old_dist_info_vars['mean']
        old_log_stds = old_dist_info_vars['log_std']
        new_means = new_dist_info_vars['mean']
        new_log_stds = new_dist_info_vars['log_std']

        old_std = tf.exp(old_log_stds)
        new_std = tf.exp(new_log_stds)

        numerator = tf.square(old_means - new_means) + tf.square(old_std) - tf.square(new_std)
        denominator = 2 * tf.square(new_std) + 1e-8
        return tf.reduce_sum(numerator / denominator + new_log_stds - old_log_stds, reduction_indices=-1)

    def likelihood_ratio_sym(self, x_var, old_dist_info_vars, new_dist_info_vars):
        logli_new = self.log_likelihood_sym(x_var, new_dist_info_vars)
        logli_old = self.log_likelihood_sym(x_var, old_dist_info_vars)
        return tf.exp(logli_new - logli_old + 1e-6)

    def log_likelihood_sym(self, x_var, dist_info_vars):
        means = dist_info_vars['mean']
        log_stds = dist_info_vars['log_std']
        zs = (x_var - means) / tf.exp(log_stds)
        return - tf.reduce_sum(log_stds, axis=-1) \
               - 0.5 * tf.reduce_sum(tf.square(zs), axis=-1) \
               - 0.5 * self.dim * np.log(2 * np.pi)

    def sample(self, dist_info):
        means = dist_info['mean']
        log_stds = dist_info['log_std']
        rnd = np.random.normal(size=means.shape)
        return rnd * tf.exp(log_stds) + means

    def log_likelihood(self, xs, dist_info):
        means = dist_info['mean']
        log_stds = dist_info['log_std']
        zs = (xs - means) / tf.exp(log_stds)
        return - np.sum(log_stds, axis=-1) - 0.5 * np.sum(np.square(zs), axis=-1) - 0.5 * self.dim * np.log(2 * np.pi)

    def entropy(self, dist_info):
        log_stds = dist_info['log_std']
        return tf.reduce_sum(log_stds + np.log(np.sqrt(2 * np.pi * np.e)), axis=-1)

    @property
    def dist_info_specs(self):
        return [('mean', (self.dim, )), ('log_std', (self.dim, ))]



