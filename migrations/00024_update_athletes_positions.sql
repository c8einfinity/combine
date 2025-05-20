DROP TABLE IF EXISTS position_mapping;

CREATE TABLE position_mapping (
                                            abbreviation VARCHAR(10),
                                            full_name VARCHAR(50)
);

-- Insert the mapping of abbreviations to full names
INSERT INTO position_mapping (abbreviation, full_name)
VALUES
    ('QB', 'Quarterback'),
    ('RB', 'Running Back'),
    ('FB', 'Fullback'),
    ('WR', 'Wide Receiver'),
    ('WRS', 'Wide Receiver'),
    ('TE', 'Tight End'),
    ('OLG', 'Offensive Lineman/Guard'),
    ('OG', 'Offensive Lineman/Guard'),
    ('OLT', 'Offensive Lineman/Tackle'),
    ('OT', 'Offensive Lineman/Tackle'),
    ('OLC', 'Offensive Lineman/Center'),
    ('Center', 'Offensive Lineman/Center'),
    ('DL', 'Defensive Lineman'),
    ('DL1T', 'Defensive Lineman'),
    ('DL2T', 'Defensive Lineman'),
    ('DL3T', 'Defensive Lineman'),
    ('DL5T', 'Defensive Lineman'),
    ('LB', 'Linebacker'),
    ('ILB', 'Linebacker'),
    ('OLB', 'Linebacker'),
    ('CB', 'Cornerback'),
    ('CBN', 'Cornerback'),
    ('S', 'Safety'),
    ('ER', 'Edge Rusher'),
    ('EDGE', 'Edge Rusher'),
    ('DE/EDGE', 'Edge Rusher'),
    ('K', 'Kicker'),
    ('P', 'Punter'),
    ('H', 'Holder'),
    ('LS', 'Long Snapper'),
    ('G', 'Gunner'),
    ('U', 'Upback'),
    ('ST', 'Special Teamer'),
    ('DB', 'Defensive Back');

-- Update the athlete positions in your main table
UPDATE player
SET position = (
    SELECT full_name
    FROM position_mapping
    WHERE position_mapping.abbreviation = player.position
)
WHERE EXISTS (
    SELECT 1
    FROM position_mapping
    WHERE position_mapping.abbreviation = player.position
);

UPDATE player
SET sport = 'American Football'
WHERE sport = 'Football';

-- Drop the mapping table after the update
DROP TABLE IF EXISTS position_mapping;