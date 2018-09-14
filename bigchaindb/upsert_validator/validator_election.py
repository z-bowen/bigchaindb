# Copyright BigchainDB GmbH and BigchainDB contributors
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from bigchaindb.common.exceptions import InvalidPowerChange
from bigchaindb.elections.election import Election
from bigchaindb.common.schema import TX_SCHEMA_VALIDATOR_ELECTION
from .validator_utils import (new_validator_set, encode_validator, validate_asset_public_key)


class ValidatorElection(Election):

    OPERATION = 'VALIDATOR_ELECTION'
    # NOTE: this transaction class extends create so the operation inheritence is achieved
    # by renaming CREATE to VALIDATOR_ELECTION
    CREATE = OPERATION
    ALLOWED_OPERATIONS = (OPERATION,)
    TX_SCHEMA_CUSTOM = TX_SCHEMA_VALIDATOR_ELECTION

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
    def validate_schema(cls, tx):
        super(ValidatorElection, cls).validate_schema(tx)
        validate_asset_public_key(tx['asset']['data']['public_key'])

    def change_validator_set(self, bigchain, new_height):
        # The new validator set comes into effect from height = new_height+1
        # (upcoming changes to Tendermint will change this to height = new_height+2)
        validator_updates = [self.asset['data']]
        curr_validator_set = bigchain.get_validators(new_height)
        updated_validator_set = new_validator_set(curr_validator_set,
                                                  validator_updates)

        updated_validator_set = [v for v in updated_validator_set if v['voting_power'] > 0]
        bigchain.store_validator_set(new_height+1, updated_validator_set)
        return encode_validator(self.asset['data'])

    @classmethod
    def on_approval(cls, bigchain, election, new_height):
        pass
