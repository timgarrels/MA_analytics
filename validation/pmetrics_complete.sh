PMETRICS_OUT=$1

REAL_LENGTH=$(wc -l < $1/pAnchorNodeDistance/graphlet_metrics)
EXPECTED_LENGTH=$(head -n 1 $1/pAnchorNodeDistance/graphlet_metrics)
EXPECTED_LENGTH=$((EXPECTED_LENGTH+1))

[[ $EXPECTED_LENGTH -eq $REAL_LENGTH ]]
pAnchorNodeDistance=$?

REAL_LENGTH=$(wc -l < $1/pDegree/graphlet_metrics)
EXPECTED_LENGTH=$(head -n 1 $1/pDegree/graphlet_metrics)
EXPECTED_LENGTH=$((EXPECTED_LENGTH+1))

[[ $EXPECTED_LENGTH -eq $REAL_LENGTH ]]
pDegree=$?

REAL_LENGTH=$(wc -l < $1/pGraphModuleParticipation/graphlet_metrics)
EXPECTED_LENGTH=$(head -n 1 $1/pGraphModuleParticipation/graphlet_metrics)
EXPECTED_LENGTH=$((EXPECTED_LENGTH+1))

[[ $EXPECTED_LENGTH -eq $REAL_LENGTH ]]
pGraphModuleParticipation=$?


if [[ $pAnchorNodeDistance -ne 0 || $pDegree -ne 0 || $pGraphModuleParticipation -ne 0 ]]; then
  echo $PMETRICS_OUT
fi