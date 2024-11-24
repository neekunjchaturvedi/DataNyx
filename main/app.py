import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import google.generativeai as genai
import random


# Load the saved model and scaler
@st.cache_resource
def load_models():
    knn_model = joblib.load('loan_repayment_knn_model.joblib')
    scaler = joblib.load('loan_repayment_scaler.joblib')
    return knn_model, scaler

def calculate_achievements(loan_amount, monthly_payment, interest_rate, months):
    """Calculate various achievements and their unlock dates"""
    achievements = []
    
    # Time-based achievements
    time_achievements = {
        3: "Quarter Year Milestone 🌱",
        6: "Half Year Champion 🌿",
        12: "One Year Strong 🌳",
        24: "Two Year Warrior 🏆",
        36: "Three Year Victor 👑",
        60: "Five Year Master 🎯",
        120: "Decade Dedication 💫"
    }
    
    # Amount-based achievements
    amount_achievements = {
        0.1: "10% Progress Pioneer 🎯",
        0.25: "Quarter Way Hero 🌟",
        0.5: "Halfway Champion 🏆",
        0.75: "Three-Quarter Milestone 💫",
        0.9: "90% Achievement Unlocked 👑",
        1.0: "Loan Conquered! 🎉"
    }
    
    # Calculate monthly progress
    remaining_balance = loan_amount
    monthly_rate = interest_rate / 1200
    
    for month in range(1, months + 1):
        # Calculate remaining balance
        interest = remaining_balance * monthly_rate
        principal = monthly_payment - interest
        remaining_balance -= principal
        
        # Check time-based achievements
        if month in time_achievements:
            achievements.append({
                'month': month,
                'title': time_achievements[month],
                'type': 'time',
                'description': f"Successfully made payments for {month} months!",
                'amount_paid': loan_amount - remaining_balance,
                'percentage': ((loan_amount - remaining_balance) / loan_amount) * 100
            })
        
        # Check amount-based achievements
        progress = (loan_amount - remaining_balance) / loan_amount
        for threshold, title in amount_achievements.items():
            if progress >= threshold and not any(a['title'] == title for a in achievements):
                achievements.append({
                    'month': month,
                    'title': title,
                    'type': 'amount',
                    'description': f"Paid off {threshold*100:.0f}% of your loan!",
                    'amount_paid': loan_amount - remaining_balance,
                    'percentage': progress * 100
                })
    
    return sorted(achievements, key=lambda x: x['month'])

# Calculate suggested repayment period based on financial ratios
def suggest_repayment_period(loan_amount, monthly_income, monthly_expenses, interest_rate):
    
    annual_income = monthly_income * 12
    disposable_income = monthly_income - monthly_expenses
    
  
    loan_to_income_ratio = loan_amount / annual_income
    
    
    if loan_to_income_ratio <= 1:  
        base_period = 60 
    elif loan_to_income_ratio <= 2:
        base_period = 120  
    elif loan_to_income_ratio <= 3:
        base_period = 180 
    else:
        base_period = 240  
        
    # Adjust based on disposable income
    disposable_income_ratio = disposable_income / monthly_income
    if disposable_income_ratio > 0.5:  # High disposable income
        base_period = max(base_period * 0.8, 36)  # Shorter period, minimum 3 years
    elif disposable_income_ratio < 0.2:  # Low disposable income
        base_period = min(base_period * 1.2, 360)  # Longer period, maximum 30 years
        
    # Adjust for interest rate
    if interest_rate > 10:
        base_period = min(base_period * 1.1, 360)  # Higher rates → longer period
    elif interest_rate < 5:
        base_period = max(base_period * 0.9, 36)  # Lower rates → shorter period
        
    return round(base_period)

# Calculate monthly payment
def calculate_monthly_payment(loan_amount, interest_rate, months):
    r = interest_rate / 1200  # Monthly interest rate
    if r == 0:
        return loan_amount / months
    payment = loan_amount * (r * (1 + r)**months) / ((1 + r)**months - 1)
    return payment

# Calculate affordability metrics
def calculate_affordability(monthly_payment, monthly_income, monthly_expenses):
    dti_ratio = monthly_payment / monthly_income
    total_burden = (monthly_payment + monthly_expenses) / monthly_income
    savings_potential = monthly_income - monthly_expenses - monthly_payment
    
    affordability_score = 0
    if dti_ratio < 0.28:
        affordability_score += 33
    elif dti_ratio < 0.43:
        affordability_score += 20
        
    if total_burden < 0.7:
        affordability_score += 33
    elif total_burden < 0.8:
        affordability_score += 20
        
    if savings_potential > monthly_income * 0.2:
        affordability_score += 34
    elif savings_potential > 0:
        affordability_score += 20
        
    return {
        'dti_ratio': dti_ratio,
        'total_burden': total_burden,
        'savings_potential': savings_potential,
        'affordability_score': affordability_score
    }

st.set_page_config(page_title="Loan Repayment Predictor", layout="wide")
    
st.header("🏦 Forecasting Timeline of Overseas Loan")
st.markdown("---")


col1, col2 = st.columns(2)

with col1:
    st.subheader("Loan Details")
    loan_amount = st.number_input("Loan Amount (USD)", min_value=1000, max_value=1000000, value=250000, step=1000)
    interest_rate = st.slider("Interest Rate (%)", min_value=1.0, max_value=20.0, value=8.0, step=0.1)
    start_date = st.date_input("Start Date", datetime.now())
    
with col2:
    st.subheader("Financial Information")
    monthly_income = st.number_input("Monthly Income (USD)", min_value=1000, max_value=100000, value=15000, step=100)
    monthly_expenses = st.number_input("Monthly Expenses (USD)", min_value=0, max_value=monthly_income, value=8000, step=100)

if st.button("Calculate Repayment Options", type="primary"):
    
    suggested_months = suggest_repayment_period(loan_amount, monthly_income, monthly_expenses, interest_rate)
    
    # Calculate payments for different terms
    terms = {
        'Short': max(suggested_months - 60, 36),
        'Recommended': suggested_months,
        'Long': min(suggested_months + 60, 360)
    }
    
    # Calculate payments and metrics for each term
    options = {}
    for term_name, months in terms.items():
        monthly_payment = calculate_monthly_payment(loan_amount, interest_rate, months)
        total_interest = (monthly_payment * months) - loan_amount
        affordability = calculate_affordability(monthly_payment, monthly_income, monthly_expenses)
        
        options[term_name] = {
            'months': months,
            'monthly_payment': monthly_payment,
            'total_interest': total_interest,
            'affordability': affordability
        }
    
    
    st.markdown("---")
    st.subheader("📊 Repayment Options")
    
    # Create columns for each option
    cols = st.columns(len(options))
    
    for idx, (term_name, data) in enumerate(options.items()):
        with cols[idx]:
            st.markdown(f"### {term_name} Term")
            st.metric(
                "Repayment Period",
                f"{data['months']} months",
                f"({data['months']/12:.1f} years)"
            )
            st.metric(
                "Monthly Payment",
                f"${data['monthly_payment']:,.2f}",
                f"{(data['monthly_payment']/monthly_income*100):.1f}% of income"
            )
            st.metric(
                "Total Interest",
                f"${data['total_interest']:,.2f}",
                f"{(data['total_interest']/loan_amount*100):.1f}% of principal"
            )
            st.progress(data['affordability']['affordability_score'] / 100)
            st.markdown(f"Affordability Score: {data['affordability']['affordability_score']}%")
    
    
    # Show comparison chart
    st.markdown("---")
    st.subheader("📈 Payment Comparison")
    
    comparison_data = []
    for term_name, data in options.items():
        comparison_data.append({
            'Term': term_name,
            'Monthly Payment': data['monthly_payment'],
            'Total Interest': data['total_interest'],
            'Total Cost': data['monthly_payment'] * data['months']
        })
    
    df_comparison = pd.DataFrame(comparison_data)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Monthly Payment',
        x=df_comparison['Term'],
        y=df_comparison['Monthly Payment'],
        text=df_comparison['Monthly Payment'].apply(lambda x: f'${x:,.2f}'),
        textposition='auto',
    ))
    
    fig.update_layout(
        title="Monthly Payment Comparison",
        yaxis_title="Amount (USD)",
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Monthly Payment Breakdown
        fig_pie = go.Figure(data=[
            go.Pie(
                labels=['Principal', 'Interest'],
                values=[loan_amount, monthly_payment * months - loan_amount],
                hole=.3
            )
        ])
        fig_pie.update_layout(title="Total Payment Breakdown")
        st.plotly_chart(fig_pie, use_container_width=True)
    with chart_col2:
        # Monthly Cash Flow
        cash_flow_data = pd.DataFrame({
            'Category': ['Income', 'Expenses', 'Loan Payment', 'Remaining'],
            'Amount': [
                monthly_income,
                monthly_expenses,
                monthly_payment,
                monthly_income - monthly_expenses-monthly_payment
            ]
        })
        fig_bar = px.bar(
            cash_flow_data,
            x='Category',
            y='Amount',
            title="Monthly Cash Flow Analysis"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Financial Health Analysis
    st.markdown("---")
    st.subheader("💹 Financial Health Analysis")
    
    recommended_data = options['Recommended']
    health_cols = st.columns(3)
    
    with health_cols[0]:
        dti = recommended_data['affordability']['dti_ratio']
        st.metric(
            "Debt-to-Income Ratio",
            f"{dti*100:.1f}%",
            "Good" if dti < 0.43 else "High"
        )
        
    with health_cols[1]:
        burden = recommended_data['affordability']['total_burden']
        st.metric(
            "Total Monthly Burden",
            f"{burden*100:.1f}%",
            "Good" if burden < 0.8 else "High"
        )
        
    with health_cols[2]:
        savings = recommended_data['affordability']['savings_potential']
        st.metric(
            "Monthly Savings Potential",
            f"${savings:,.2f}",
            "After loan payment"
        )
    
    # Add Achievements Section
    st.markdown("---")
    st.subheader("🏆 Loan Payment Achievements")
    
    # Calculate achievements for all terms
    term_achievements = {}
    for term_name, data in options.items():
        achievements = calculate_achievements(
            loan_amount,
            data['monthly_payment'],
            interest_rate,
            data['months']
        )
        term_achievements[term_name] = achievements
    
    # Create tabs for different terms
    term_tabs = st.tabs(list(options.keys()))
    
    for tab, term_name in zip(term_tabs, options.keys()):
        with tab:
            achievements = term_achievements[term_name]
            
            # Create achievement timeline visualization
            fig = go.Figure()
            
            # Add achievement markers
            fig.add_trace(go.Scatter(
                x=[a['month'] for a in achievements],
                y=[a['percentage'] for a in achievements],
                mode='markers+text',
                marker=dict(
                    size=20,
                    symbol='star',
                    color=['gold' if a['type'] == 'amount' else 'silver' for a in achievements]
                ),
                text=[a['title'].split()[0] for a in achievements],
                textposition='top center',
                name='Achievements'
            ))
            
            # Add progress line
            months = list(range(0, options[term_name]['months'] + 1))
            progress = [min(100 * i * options[term_name]['monthly_payment'] / loan_amount, 100) for i in months]
            
            fig.add_trace(go.Scatter(
                x=months,
                y=progress,
                mode='lines',
                line=dict(color='rgba(0,100,255,0.3)'),
                name='Loan Progress'
            ))
            
            fig.update_layout(
                title=f"Achievement Timeline - {term_name} Term",
                xaxis_title="Months",
                yaxis_title="Loan Progress (%)",
                yaxis_range=[0, 105],
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display achievement details in an expandable section
            with st.expander("View Detailed Achievements"):
                for achievement in achievements:
                    st.markdown(f"""
                    ### {achievement['title']}
                    - 📅 **Month:** {achievement['month']} ({achievement['month']/12:.1f} years)
                    - 💰 **Amount Paid:** ${achievement['amount_paid']:,.2f}
                    - 📊 **Progress:** {achievement['percentage']:.1f}%
                    - 📝 **Description:** {achievement['description']}
                    ---
                    """)
            
            # Display next upcoming achievement
            current_month = 1  
            upcoming = next((a for a in achievements if a['month'] > current_month), None)
            if upcoming:
                st.markdown("### 🎯 Next Achievement")
                months_until = upcoming['month'] - current_month
                st.info(f"""
                **{upcoming['title']}**
                - Unlocks in {months_until} months
                - At {upcoming['percentage']:.1f}% loan progress
                - When ${upcoming['amount_paid']:,.2f} is paid
                """)
    
    # Add recommendations
    st.markdown("---")
    st.subheader("💡 Recommendations")
    
    if recommended_data['affordability']['affordability_score'] >= 80:
        st.success("✅ This loan appears to be within your affordable range.")
    elif recommended_data['affordability']['affordability_score'] >= 60:
        st.warning("⚠️ This loan is manageable but may strain your finances.")
    else:
        st.error("❌ This loan may be difficult to manage with your current financial situation.")
        
    recommendations = []
    if dti > 0.43:
        recommendations.append("Consider a longer term to reduce monthly payments")
    if burden > 0.8:
        recommendations.append("Look for ways to reduce monthly expenses")
    if savings < monthly_income * 0.1:
        recommendations.append("Build an emergency fund before taking the loan")
        
    if recommendations:
        st.markdown("**Suggested Actions:**")
        for rec in recommendations:
            st.markdown(f"- {rec}")


    
genai.configure(api_key='AIzaSyCd2CAIpKTet21_w5TQKh7TSj3J2jA5iro')
def generate_response(prompt):
    try:
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        chat = model.start_chat()

        
        response = chat.send_message(prompt)

        
        return response.text  
    except Exception as e:
        return f"Error generating response: {e}"
st.write("Get the best recommendations based on your loan repayment")
if st.button("Recommend"):
    x = f"Given a loan of {loan_amount} USD with an interest rate of {interest_rate}% and a monthly repayment  " \
    f"what repayment strategies would you recommend to ensure that the user can complete the repayment months " \
    f"without getting into financial trouble or falling into debt? also give a few financial aids such as scholarship emergency fund etc"
    ai_response = generate_response(x)  
    st.write(ai_response)


def generate_random_link():
    domains = ['linkedin.com/jobs', 'indeed.com', 'glassdoor.com', 'monster.com', 'dice.com']
    paths = ['software', 'tech', 'engineering', 'developer', 'programming']
    return f"https://www.{random.choice(domains)}/{random.choice(paths)}/"

if st.button("Find Software Jobs"):
    # Title and description
    st.title("💻 Unique Software Jobs")
    st.write("Discover some specialized roles in the software industry!")

    # Create DataFrame with software jobs information
    jobs_data = {
        'Job Title': [
            'ML Operations Engineer',
            'Blockchain Developer',
            'Game Physics Programmer',
            'Computer Vision Engineer',
            'Quantum Computing Developer'
        ],
        'Annual Salary Range': [
            '$120,000 - $180,000',
            '$130,000 - $200,000',
            '$95,000 - $150,000',
            '$110,000 - $170,000',
            '$150,000 - $250,000'
        ],
        'Description': [
            'Builds and maintains machine learning infrastructure, ensures smooth deployment of ML models, and optimizes ML pipelines for production environments.',
            'Develops and implements blockchain protocols, smart contracts, and decentralized applications (dApps) using technologies like Ethereum and Solidity.',
            'Creates realistic physics simulations for video games, implements physics engines, and optimizes performance for real-time gaming experiences.',
            'Develops algorithms for image and video processing, implements object detection systems, and creates computer vision solutions for autonomous systems.',
            'Develops quantum algorithms, works with quantum computing frameworks, and optimizes code for quantum hardware architectures.'
        ]
    }

    # Convert to DataFrame
    df = pd.DataFrame(jobs_data)

    # Display each job in an expander with random links
    for idx, row in df.iterrows():
        with st.expander(f"💼 {row['Job Title']} | {row['Annual Salary Range']}", expanded=False):
            st.write(row['Description'])
            job_links = [generate_random_link() for _ in range(3)]
            st.write("### Sample Job Listings:")
            for i, link in enumerate(job_links, 1):
                st.markdown(f"{i}. [Apply Here - Company {random.randint(1, 100)}]({link})")
            
    # Add some statistics
    st.sidebar.header("Quick Facts")
    st.sidebar.info(f"""
    - Total Jobs Showcased: {len(df)}
    - Highest Potential Salary: $250,000
    - Average Minimum Salary: ${sum([int(range.split(' - ')[0].replace('$','').replace(',','')) for range in df['Annual Salary Range']])/len(df):,.2f}
    - Industry: Software & Technology
    - Required Experience: 3-5 years average
    """)

    # Footer
    st.markdown("---")
    st.markdown("""
    *Salary ranges are approximate and may vary based on location, experience, and company.*  
    *Job listings are randomly generated for demonstration purposes.*
    """)