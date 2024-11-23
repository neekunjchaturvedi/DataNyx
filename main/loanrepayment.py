import streamlit as st
import numpy as np


def generate_recommendations(loan_amount, income, monthly_payment, interest_rate):
   
    dti_ratio = monthly_payment / (income / 12)  
    loan_to_income_ratio = loan_amount / income  

   
    if interest_rate > 0:
        monthly_interest_rate = interest_rate / 100 / 12
        denominator = monthly_payment - loan_amount * monthly_interest_rate
        
        if denominator <= 0:  
            months_to_repay = float('inf')
        else:
            months_to_repay = np.log(monthly_payment / denominator) / np.log(1 + monthly_interest_rate)
    else:
        if monthly_payment == 0:  
            months_to_repay = float('inf')  
        else:
            months_to_repay = loan_amount / monthly_payment

    
    if months_to_repay != float('inf'):
        months_to_repay = int(np.ceil(months_to_repay))

   
    recommendations = []
    if dti_ratio > 0.4:
        recommendations.append("Consider lowering monthly payments by extending the loan term.")
    if loan_to_income_ratio > 0.6:
        recommendations.append("Evaluate ways to increase income or reduce loan amount.")
    if interest_rate > 5:
        recommendations.append("Explore refinancing options for a lower interest rate.")

    return months_to_repay, recommendations


st.title("Loan Repayment Recommendation System")
st.markdown("This app calculates the loan repayment timeline and provides tailored recommendations.")


st.sidebar.header("User Input Parameters")
loan_amount = st.sidebar.number_input("Loan Amount (USD)", min_value=1000, max_value=1000000, step=1000, value=500000)
income = st.sidebar.number_input("Annual Income (USD)", min_value=1000, max_value=1000000, step=1000, value=60000)
monthly_payment = st.sidebar.number_input("Monthly Payment (USD)", min_value=100, max_value=100000, step=100, value=8000)
interest_rate = st.sidebar.slider("Interest Rate (%)", min_value=0.0, max_value=20.0, step=0.1, value=3.0)


months_to_repay, recommendations = generate_recommendations(loan_amount, income, monthly_payment, interest_rate)


st.write("### Loan Repayment Timeline")
if months_to_repay == float('inf'):
    st.write("The current loan setup is not feasible. Please adjust the inputs.")
else:
    st.write(f"The estimated repayment timeline is **{months_to_repay} months** ({months_to_repay / 12:.2f} years).")

st.write("### Recommendations")
if recommendations:
    for i, rec in enumerate(recommendations, 1):
        st.write(f"{i}. {rec}")
else:
    st.write("No specific recommendations. Your financial setup looks good!")

st.button("Get More Recommendations")


def generate_repayment_schedule(loan_amount, monthly_payment, interest_rate):
    balances = []
    months = []
    remaining_balance = loan_amount
    monthly_interest_rate = interest_rate / 100 / 12 if interest_rate > 0 else 0
    while remaining_balance > 0 and len(months) < 500:  
        interest = remaining_balance * monthly_interest_rate
        principal = monthly_payment - interest
        if principal > remaining_balance:
            principal = remaining_balance
        remaining_balance -= principal
        months.append(len(months) + 1)
        balances.append(remaining_balance)
    return months, balances

months, balances = generate_repayment_schedule(loan_amount, monthly_payment, interest_rate)



monthly_income = income / 12
dti_ratio = monthly_payment / monthly_income
loan_to_income_ratio = loan_amount / income


st.write("### Calculated Metrics")
st.write(f"**Debt-to-Income (DTI) Ratio**: {dti_ratio:.2f}")
st.write(f"**Loan-to-Income (LTI) Ratio**: {loan_to_income_ratio:.2f}")
st.write(f"**Interest Rate**: {interest_rate:.2f}%")
st.write("### Insights Visualization")


if balances:
    st.line_chart({"Remaining Balance (USD)": balances})


repayment_timelines = [loan_amount / (monthly_payment if monthly_payment > 0 else 1)]  # Avoid divide by zero
loan_amounts = np.linspace(100000, 800000, 10)

st.write("#### Loan Amount vs. Repayment Timeline")
st.line_chart({
    "Loan Amount (USD)": loan_amounts,
    "Repayment Timeline (Months)": [amt / monthly_payment for amt in loan_amounts if monthly_payment > 0]
})
