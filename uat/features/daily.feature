Feature: Daily Gomoku command-line acceptance
  The maintained game must complete, persist, and replay without a mocked product boundary.

  Scenario: Play, record, and replay a complete seeded game
    Given a clean temporary record directory
    When I play seeded game 7 through the real command line
    Then the game command succeeds
    And the saved game contains legal coordinate pairs
    And the saved game reaches a terminal result
    When I replay the generated record through the real command line
    Then the replay command succeeds
    And the replay terminal result matches the game
