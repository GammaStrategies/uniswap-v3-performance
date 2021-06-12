# Analytics

## VISR Token Endpoints
### GET /visr/basicStats
Returns basic stats about the VISR token

Response:
```json
{
	"priceUSD": 1.0422319100795823, 
	"totalDistributed": 225157.93851120802, 
	"totalDistributedUSD": 354463.44960261334, 
	"totalStaked": 13531192.19599181, 
	"totalSupply": 100000000.0
}
```
### Get /visr/yield
Returns yield related data for the VISR token

Daily is calculated using the most recent day data.

Weekly is calculated using the most recent 7 day data.

Monthly is calculated using the most recent 30 day data.

Response:
```json
{
	"daily": {
		"apy": 0.1517809650893731, 
		"estimatedAnnualDistribution": 2053777.410317091, 
		"estimatedAnnualDistributionUSD": 2247482.29752211, 
		"yield": 0.00041583826051883044
	},
	"weekly": {
		"apy": 0.13972700006103891, 
		"estimatedAnnualDistribution": 1865138.9157595846, 
		"estimatedAnnualDistributionUSD": 2534726.2017299226, 
		"yield": 0.0026796958915815683
	},
	"monthly": {
		"apy": 0.30411554158684123, 
		"estimatedAnnualDistribution": 3424276.9815246225, 
		"estimatedAnnualDistributionUSD": 5390798.296039745, 
		"yield": 0.019996638350915585
	}
}
```
### GET /visr/dailyDistribution
Returns the amount of VISR distributed per day.

5 days by default, this can be adjusted by sending the days parameter

Response:
```json
{
"dailyDistribution": [
	{
		"date": "2021-06-11T00:00:00", 
		"distributed": 5626.787425526277, 
		"timestamp": 1623369600
	}, 
	{
		"date": "2021-06-10T00:00:00", 
		"distributed": 5543.0, 
		"timestamp": 1623283200
	}, 
	{
		"date": "2021-06-09T00:00:00", 
		"distributed": 3816.0, 
		"timestamp": 1623196800
	}, 
	{
		"date": "2021-06-08T00:00:00", 
		"distributed": 6461.999999999999, 
		"timestamp": 1623110400
	}, 
	{
		"date": "2021-06-07T00:00:00", 
		"distributed": 4467.0, 
		"timestamp": 1623024000
	}
  ], 
  "nDays": 5
}
```

## Uniswap V3 Hypervisor endpoints

### GET /hypervisors/aggregateStats
totalFeesClaimedUSD is USD

TVL has a 400k buffer at the moment to take into account closed beta positions

Response:
```json
{
	"pairCount": 2, 
	"totalFeesClaimedUSD": 12841.893746720685, 
	"totalValueLockedUSD": 1052607.6932798002
}
```

### GET /hypervisors/recentFees
Returns  fees collected in the last 24 hours.  The period can be modified by sending the hours parameter.

Response:
```json
{
	"fees": {
		"grossFeesUSD": 8072.334992053622, 
		"grossFeesVISR": 7752.871811219713, 
		"netFeesUSD": 7265.101494049108, 
		"netFeesVISR": 6977.584631251066, 
		"protocolFeesUSD": 807.233498004513, 
		"protocolFeesVISR": 775.2871799686459
	}, 
	"periodHours": 24
}
```

### GET /hypervisor/<hypervisorAddress>/returns
Get stats related to returns calculated using the most recent daily/weekly/monthly data

Response:
```json
{
	"hypervisor": "0x9a98bffabc0abf291d6811c034e239e916bbcec0", 
	"returns": {
		"daily": {
			"cumFeeReturn": 0.012640184493185824, 
			"feeApr": 4.656187384531289, 
			"feeApy": 102.18029213532452, 
			"totalPeriodSeconds": 85611.0
		}, 
		"monthly": {
			"cumFeeReturn": 0.07161614564526353, 
			"feeApr": 6.352486355699216, 
			"feeApy": 543.3968639875819, 
			"totalPeriodSeconds": 355528.0
		}, 
		"weekly": {
			"cumFeeReturn": 0.07161614564526353, 
			"feeApr": 6.352486355699216, 
			"feeApy": 543.3968639875819, 
			"totalPeriodSeconds": 355528.0
		}
	}
}
```

## Bollinger Bands

### GET /bollingerBandsChartData
To get bollinger bands for a specific pool
with these paramaters:
poolAddress: address of pool
periodHours: The total period in hours
