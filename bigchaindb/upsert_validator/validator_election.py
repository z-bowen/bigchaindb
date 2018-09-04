# Copyright BigchainDB GmbH and BigchainDB contributors
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from bigchaindb.common.exceptions import InvalidPowerChange
from bigchaindb.common.election import Election
from bigchaindb.common.schema import (_validate_schema,
                                      TX_SCHEMA_VALIDATOR_ELECTION)
from .validator_utils import (new_validator_set, encode_validator)


class ValidatorElection(Election):

    ELECTION_TYPE = 'VALIDATOR_ELECTION'
    # NOTE: this transaction class extends create so the operation inheritence is achieved
    # by renaming CREATE to VALIDATOR_ELECTION
    CREATE = ELECTION_TYPE
    ALLOWED_OPERATIONS = (ELECTION_TYPE,)

    def validate(self, bigchain, current_transactions=[]):
        """For more details refer BEP-21: https://github.com/bigchaindb/BEPs/tree/master/21
        """

        current_validators = self.get_validators(bigchain)

        super(ValidatorElection, self).validate(bigchain, current_transactions=current_transactions)

        # NOTE: change more than 1/3 of the current power is not allowed
        if self.asset['data']['power'] >= (1/3)*sum(current_validators.values()):
            raise InvalidPowerChange('`power` change must be less than 1/3 of total power')

        return self

    @classmethod
    def validate_schema(cls, tx, skip_id=False):
        """Validate the validator election transaction. Since `VALIDATOR_ELECTION` extends `ELECTION`
           transaction, all the validations for `ELECTION` transaction are covered by `super`
        """

        super(ValidatorElection, cls).validate_schema(tx, skip_id=skip_id)

        _validate_schema(TX_SCHEMA_VALIDATOR_ELECTION, tx)

    @classmethod
    def on_approval(cls, bigchain, election, new_height):
        # The new validator set comes into effect from height = new_height+1
        validator_updates = [election.asset['data']]
        curr_validator_set = bigchain.get_validators(new_height)
        updated_validator_set = new_validator_set(curr_validator_set,
                                                  validator_updates)

        updated_validator_set = [v for v in updated_validator_set if v['voting_power'] > 0]
        bigchain.store_validator_set(new_height+1, updated_validator_set, election.id)
        return [encode_validator(election.asset['data'])]
