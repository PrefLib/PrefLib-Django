def my_assert(condition, error, error_list):
    try:
        assert condition
    except AssertionError:
        print("ERROR: " + str(error))
        error_list.append(error)


def basic_numbers(instance):
    """ Checks that the basic numbers (voters, alternatives, distinct orders etc...) are aligned with the order of the
        instance.

        :param instance: The instance to draw.
        :type instance: :class:`preflibtools.instances.preflibinstance.OrdinalInstance`
    """

    error_list = []

    my_assert(len(instance.orders) == len(instance.multiplicity),
              "len(orders) {} differs from len(order_multiplicity) {}".format(
                  len(instance.orders), len(instance.multiplicity)),
              error_list)

    if instance.data_type in ["soc", "toc", "toi", "soi"]:
        my_assert(instance.num_voters == sum(multiplicity for multiplicity in instance.multiplicity.values()),
                  "Number of voters {} and number of orders seem different {}".format(
                      instance.num_voters, sum(multiplicity for multiplicity in instance.multiplicity.values())),
                  error_list)

    my_assert(instance.num_unique_orders == len(instance.orders),
              "Number of unique order {} differs from len(orders) {}".format(
                  instance.num_unique_orders, len(instance.orders)),
              error_list)

    alternatives = set(alt for order in instance.orders for indif_class in order for alt in indif_class)
    my_assert(len(alternatives) <= instance.num_alternatives,
              "More alternatives appear in the orders {} than in the header {}".format(
                  len(alternatives), instance.num_alternatives),
              error_list)

    my_assert(instance.num_alternatives == len(instance.alternatives_name),
              "Number of alternatives {} differs from number of alternative names {}".format(
                  instance.num_alternatives, len(instance.alternatives_name)),
              error_list)

    my_assert(len(set(instance.alternatives_name.values())) == instance.num_alternatives,
              "Some alternatives have the same name: {} != {}".format(
                  len(set(instance.alternatives_name.values())), instance.num_alternatives),
              error_list)

    return error_list


def orders(instance):
    """ Checks that the orders are consistent.

        :param instance: The instance to draw.
        :type instance: :class:`preflibtools.instances.preflibinstance.OrdinalInstance`
    """

    error_list = []

    if instance.data_type in ["soc", "toc", "soi", "toi"]:
        for i in range(len(instance.orders)):
            order = instance.orders[i]
            my_assert(len([alt for indif_class in order for alt in indif_class]) <= instance.num_alternatives,
                      "Order {} at position {} has too many alternatives".format(order, i),
                      error_list)

            alternatives_appearing = [alt for indif_class in order for alt in indif_class]
            my_assert(len(alternatives_appearing) <= len(set(alternatives_appearing)),
                      "Some alternatives appear several times in order {} at position {}".format(order, i),
                      error_list)

            if instance.data_type in ["soc", "toc"]:
                my_assert(len(set(alt for indif_class in order for alt in indif_class)) <= instance.num_alternatives,
                          "Order {} at position {} does not seem complete".format(order, i),
                          error_list)

            if instance.data_type in ["soc", "soi"]:
                my_assert(max(len(indif_class) for indif_class in order) == 1,
                          "Order {} at position {} does not seem strict".format(order, i),
                          error_list)

        my_assert(len(set(instance.orders)) == len(instance.orders),
                  "Some orders appear several times: {} != {}".format(len(set(instance.orders)), len(instance.orders)),
                  error_list)

    return error_list


def data_type(instance):
    """ Checks that the data type of the instance is consistent with the orders.

        :param instance: The instance to draw.
        :type instance: :class:`preflibtools.instances.preflibinstance.OrdinalInstance`
    """

    error_list = []

    my_assert(instance.data_type == instance.infer_type(),
              "Data type {} should actually be {}".format(instance.data_type, instance.infer_type()),
              error_list)

    return error_list
