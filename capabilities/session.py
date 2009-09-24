"""
the session capability sends a unique cookie to the other party.
if the connection is dropped, this layer will attempt to reconnect
the medium, and uses the cookie to resume the verify the session.

parameters:
 * max_reconnect_attempts
 * reconnect_attempt_timeout
 * reconnect_attempt_backoff_interval

"""

