package main

import "fmt"

func ValidatePowermetricsData(p powermetricsData, validators []func(powermetricsData) error) error {
	for _, validator := range validators {
		err := validator(p)
		if err != nil {
			return err
		}
	}
	return nil
}

// TODO: use context for validators param?
// TODO: interface for powermetrics and powercfg data?
func ValidateTimestamp(p powermetricsData) error {
	if !p.StopTime.t.After(p.StartTime.t) {
		return fmt.Errorf("Stop time %v is not later than start time %v", p.StopTime, p.StartTime)
	} else {
		return nil
	}
}

func ValidateConsumption(p powermetricsData) error {
	if p.CombinedPower <= 0 {
		return fmt.Errorf("Combined power consumption %v is not greater than 0", p.CombinedPower)
	} else {
		return nil
	}
}

func ValidateTasks(p powermetricsData) error {
	if len(p.Tasks) <= 0 {
		return fmt.Errorf("No tasks in powermetrics payload")
	} else {
		return nil
	}
}
