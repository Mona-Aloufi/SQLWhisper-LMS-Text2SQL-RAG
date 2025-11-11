# ============================================================
# 🈯 BILINGUAL TEXT LABELS (Arabic + English)
# ============================================================
text_labels = {
    "en": {
        # App title
        "app_title": "SQLWhisper",
        "app_subtitle": "Transform natural language questions into accurate SQL queries",
        
         # ============================================================
        # 🏠 Home Page Text
        # ============================================================
        "welcome_title": "👋 Welcome to SQLWhisper",
        "welcome_sub": "Easily transform your natural language questions into accurate SQL queries.<br>Start by uploading your database schema or use our default demo.",
        "feature_secure": "🔒 <strong>Secure & Private</strong> — Enterprise-grade data protection",
        "feature_ai": "🧠 <strong>AI-Powered</strong> — Advanced NLP for accurate SQL generation",
        "feature_insights": "📊 <strong>Rich Insights</strong> — Interactive visualization & analytics",
        "upload_schema_btn": "📤 Upload Schema",
        "default_schema_btn": "Continue with Default",
        "upload_success": "{file} uploaded successfully!",
        "upload_info": "Now go to the <strong>Query</strong> page to start asking questions.",
        "default_info": "Using the default demo schema.<br>Navigate to the <strong>Query</strong> page to explore and generate SQL!",
         
        # ============================================================
        # 🗄️ Data Dashboard translations
        # ============================================================
        "data_dashboard_title": "Data Dashboard",
        "data_dashboard_subtitle": "Explore your uploaded or demo database structure, tables, and columns.",
        "filter_section": "Filter Options",
        "table_selection_mode": "Table Selection Mode",
        "single_table": "Single Table",
        "multiple_tables": "Multiple Tables",
        "choose_table": "Choose a Table",
        "choose_multiple_tables": "Choose Multiple Tables",
        "no_table_selected": "No table selected yet.",
        "total_tables": "Total Tables",
        "selected_tables": "Selected Tables",
        "total_rows": "Total Rows",
        "rows_chart_title": "Number of Rows per Table",
        "schema_explorer": "Schema Explorer",
        "show_schema_details": "Show Schema Details",
        "data_preview": "Data Preview",
        "error_loading_data": "Error loading data",
        "no_database_loaded": "No database loaded yet. Please upload one from the home page.",
        "table_name": "Table Name",
        "rows_count": "Row Count",
        "database_summary": "Database Summary",
        "database_file": "Database File",
        "uploaded_success": "File uploaded successfully",
        "error_loading_dashboard": "Error loading the dashboard",
        "download_csv": "Download CSV",
        "erd_diagram": "ERD Diagram",


        # ============================================================
        # 🤖 Model Dashboard translations
        # ============================================================
        "model_dashboard_title": "Model Dashboard",
        "model_dashboard_subtitle": "Monitor your AI model's performance and query statistics.",
        "avg_confidence": "Average Confidence",
        "total_queries_label": "Total Queries",
        "execution_success_label": "Execution Success",
        "valid_syntax_label": "Valid SQL Syntax",
        "performance_over_time": "Performance Over Time",
        "query_trend": "Query Success Trend",
        "confidence_trend": "Model Confidence Trend",
        "no_history_data": "No model performance data available yet.",

        #ChatBot
        "chatbot_title": "AI Chat Assistant",
        "chatbot_subtitle": "Ask SQLWhisper’s assistant anything — from SQL help to system guidance.",
        "chatbot_greeting": "Hi! I’m your SQLWhisper Assistant 🤖",
        "chatbot_schema_question": "Would you like to upload your own database schema or continue with the default demo?",
        "upload_schema_btn": "Upload Schema",
        "use_default_btn": "Use Default Demo",
        "upload_prompt": "Upload your SQLite, DB, or CSV file",
        "uploaded_success": "uploaded successfully!",
        "chatbot_ready_after_upload": "Great! Your data is ready. You can now start asking SQL-related questions.",
        "chatbot_default_reply": "Good choice! Using the demo database — ask your first question below.",
        "chat_placeholder": "Type your question here...",
        "chat_generating": "Generating response...",
        "chat_error_no_reply": "No response received from model.",
        "chat_error_server": "Server returned an error.",
        "chat_error_connection": "Could not connect to the backend.",
        "chat_connect_instruction": "Click below to connect SQLWhisper Assistant to the backend before chatting.",
        "connect_backend": "Connect to Backend",
        "checking_connection": "Checking backend connection...",
        "backend_connected_ok": "Connected successfully to backend.",

        # Tabs
        "query_tab": "Query",
        "history_tab": "History",
        "feedback_tab": "Feedback Review",
        "dashboard_tab": "Dashboard",
        "about_tab": "About",

        # Sidebar / system
        "database_info": "Database Information",
        "load_schema": "Load Database Schema",
        "loading_schema": "Loading database schema...",
        "db_connected": "Connected to database",
        "db_failed": "Failed to load database info",

        # Headers / sections
        "ask_question": "Ask a Question",
        "quick_queries": "Quick Start Queries",
        "your_question": "Your Question",
        "placeholder": "Describe what you want to know about your data...",
        "generated_sql": "Generated SQL",
        "rate_sql": "Rate this SQL",
        "test_corrected": "Test Your Corrected SQL",
        "corrected_results": "Corrected Query Results",
        "query_results": "Query Results",
        "raw_model_output": "View Raw Model Output",
        "user_feedback_review": "User Feedback Review",
        "system_db_dashboard": "System & Database Dashboard",
        "database_overview": "Database Overview",
        "schema_details": "Schema Details",
        "query_model_insights": "Query & Model Insights",
        "about_sqlwhisper": "About SQLWhisper",
        "system_status": "System Status",

        # Buttons
        "generate_sql": " Generate SQL Query",
        "clear_results": "Clear Results",
        "looks_good": "Looks good",
        "needs_improvement": "Needs improvement",
        "execute_corrected": "Execute Corrected SQL",
        "download_corrected": "Download Corrected Query Results",
        "download_results_csv": "Download Results as CSV",
        "download_history": "Download Complete History",
        "download_feedback": "Download Feedback as CSV",

        # Inputs / feedback
        "what_was_wrong": "What was wrong?",
        "corrected_sql_optional": "Your corrected SQL (optional):",

        # Messages / statuses
        "backend_not_running": "FastAPI backend is not running! Please start the server first.",
        "start_server_cmd": "python app.py",
        "enter_question_first": "Please enter a question first.",
        "generating_sql": "Generating SQL...",
        "sql_generated_ok": "SQL query generated successfully!",
        "api_error": "API Error",
        "request_failed": "Request failed",
        "only_select_allowed": "Only SELECT queries are allowed for safety.",
        "enter_sql_before_exec": "Please enter a SQL query before executing.",
        "sql_exec_error": "SQL Execution Error",
        "query_exec_success": " Query executed successfully — showing {n_rows} rows.",
        "thanks_feedback": "Thanks for your feedback! ",
        "failed_save_feedback": "Failed to save feedback",
        "feedback_saved_down": "Feedback with correction saved ",
        "sql_syntax": "SQL Syntax",
        "valid": "VALID",
        "invalid": "INVALID",
        "execution": "Execution",
        "success": "SUCCESS",
        "failed": "FAILED",
        "results": "Results",
        "rows": "ROWS",
        "no_data": "NO DATA",
        "exec_error": "Execution Error",
        "no_raw_output": "No raw output available",
        "no_history_yet": "No history yet. Your first query will create the history file.",
        "no_query_history": "No query history yet. Start by asking questions in the Query tab!",
        "error_loading_history": "Error loading history",
        "total_queries": "Total Queries",
        "successful": "Successful",
        "valid_sql": "Valid SQL",
        "success_rate": "Success Rate",
        "feedback_total": "Total Feedback Entries",
        "filter_by_verdict": "Filter by verdict:",
        "all": "All",
        "up": "up",
        "down": "down",
        "no_feedback": "No feedback available yet.",
        "error_loading_feedback": "Error loading feedback",
        "total_tables": "Total Tables",
        "total_rows": "Total Rows",
        "query_success_trend": "Query Success Trend",
        "model_conf_trend": "Model Confidence Trend",
        "no_query_yet_run": "No query history yet. Run some queries first.",
        "error_loading_dashboard": "Error loading dashboard",
        "backend_status": "Backend Status",
        "operational": "Operational",
        "not_available": "Not Available",
        "database": "Database",
        "connected_tables": "Connected ({n_tables} tables)",
        "not_loaded": "Not Loaded",
        "confidence_unavailable": "Confidence score not available from the model.",
        "confidence_label": "Confidence: {conf}% ({label})",
        # ============================================================
        # 🧾 History & Feedback translations
        # ============================================================
        "history_columns": {
            "timestamp": "Timestamp",
            "question": "Question",
            "sql_query": "SQL Query",
            "success": "Success",
            "valid_sql": "Valid SQL",
            "rows_returned": "Rows Returned",
            "error_message": "Error Message",
            "confidence": "Confidence",
            "confidence_label": "Confidence Level"
        },
        "feedback_columns": {
            "question": "Question",
            "verdict": "Verdict",
            "reason":"Reason",
            "comment": "Comment",
            "created_at": "Created At"
        },
        "verdict_labels": {
            "up": "Looks Good",
            "down": "Needs Improvement"
        },
        "success_labels": {
            True: "Success",
            False: " Failed"
        },
        "valid_sql_labels": {
            True: " Valid",
            False: "Invalid"
        },
        "confidence_labels": {
            "High": "High",
            "Medium": "Medium",
            "Low": "Low"
        },
        "generate_summary": "Generate Summary",
        "summary_box_title": "Key Insights",
        "summary_failed": "Summary failed",
        "summary_warning": "Could not generate summary.",


        # About text (kept original English)
        "about_rich_html": """
        <div style='background: linear-gradient(135deg, #f5f0ff, #e6e6ff); padding: 2rem; border-radius: 1rem; border-left: 6px solid #8a2be2;'>
        <h3 style='color: #6a0dad; margin-top: 0;'>AI-Powered SQL Query Generation</h3>
        SQLWhisper transforms your natural language questions into precise SQL queries, 
        making database interaction intuitive and accessible to everyone.
        <h4 style='color: #6a0dad;'>Key Features:</h4>
        <ul>
        <li><strong>Natural Language Processing</strong> - Ask questions in plain English</li>
        <li><strong>Smart Schema Detection</strong> - Automatically understands your database structure</li>
        <li><strong>SQL Validation</strong> - Ensures generated queries are syntactically correct</li>
        <li><strong>Instant Execution</strong> - Run queries and see results immediately</li>
        <li><strong>Interactive Results</strong> - Filter, sort, and explore your data</li>
        </ul>
        <h4 style='color: #6a0dad;'>Technical Excellence:</h4>
        <ul>
        <li>Built with FastAPI for robust backend performance</li>
        <li>Powered by advanced open-source language models</li>
        <li>Real-time SQL syntax validation</li>
        <li>Comprehensive query history and analytics</li>
        </ul>
        </div>
        """,
    },"ar": {
        # App title
        "app_title": "SQLWhisper",
        "app_subtitle": "حوّل سؤالك العادي لاستعلام SQL جاهز",
        
        # ============================================================
        # 🏠 الصفحة الرئيسية
        # ============================================================
        "welcome_title": "👋 أهلاً بك في SQLWhisper",
        "welcome_sub": "حوّل أسئلتك باللغة الطبيعية إلى استعلامات SQL دقيقة.<br>ابدأ برفع هيكل قاعدة البيانات الخاصة بك أو استخدم النسخة التجريبية الافتراضية.",
        "feature_secure": "🔒 <strong>آمن وموثوق</strong> — حماية على مستوى المؤسسات",
        "feature_ai": "🧠 <strong>مدعوم بالذكاء الاصطناعي</strong> — معالجة لغوية متقدمة لتوليد SQL بدقة",
        "feature_insights": "📊 <strong>رؤى تحليلية غنية</strong> — تصورات ونتائج تفاعلية",
        "upload_schema_btn": "📤 رفع هيكل قاعدة البيانات",
        "default_schema_btn": "استخدام النسخة الافتراضية",
        "upload_success": "تم رفع {file} بنجاح!",
        "upload_info": "انتقل إلى صفحة <strong>الاستعلام</strong> لبدء طرح الأسئلة.",
        "default_info": "يتم استخدام النسخة التجريبية الافتراضية.<br>انتقل إلى صفحة <strong>الاستعلام</strong> للاستكشاف وإنشاء الاستعلامات.",
        # ============================================================
        # 🗄️ Data Dashboard translations
        # ============================================================
        "data_dashboard_title": "لوحة بيانات القاعدة",
        "data_dashboard_subtitle": "استكشف بنية قاعدة البيانات المرفوعة أو الافتراضية، والجداول، والأعمدة.",
        "filter_section": "خيارات التصفية",
        "table_selection_mode": "وضع اختيار الجداول",
        "single_table": "جدول واحد",
        "multiple_tables": "عدة جداول",
        "choose_table": "اختر جدولاً",
        "choose_multiple_tables": "اختر جداول متعددة",
        "no_table_selected": "لم يتم تحديد أي جدول بعد.",
        "total_tables": "إجمالي الجداول",
        "selected_tables": "الجداول المحددة",
        "total_rows": "إجمالي الصفوف",
        "rows_chart_title": "عدد الصفوف في كل جدول",
        "schema_explorer": "مستكشف المخطط",
        "show_schema_details": "عرض تفاصيل المخطط",
        "data_preview": "معاينة البيانات",
        "error_loading_data": "حدث خطأ أثناء تحميل البيانات",
        "no_database_loaded": "لم يتم تحميل أي قاعدة بيانات بعد. يرجى رفع قاعدة من الصفحة الرئيسية.",
        "table_name": "اسم الجدول",
        "rows_count": "عدد الصفوف",
        "database_summary": "ملخص قاعدة البيانات",
        "database_file": "ملف قاعدة البيانات",
        "uploaded_success": "تم رفع الملف بنجاح",
        "error_loading_dashboard": "خطأ أثناء تحميل لوحة البيانات",
        "download_csv": "تحميل البيانات كملف CSV",
        \

        # ============================================================
        # 🤖 Model Dashboard translations
        # ============================================================
        "model_dashboard_title": "لوحة أداء النموذج",
        "model_dashboard_subtitle": "راقب أداء نموذج الذكاء الاصطناعي وإحصاءات الاستعلامات.",
        "avg_confidence": "متوسط الثقة",
        "total_queries_label": "إجمالي الاستعلامات",
        "execution_success_label": "نجاح التنفيذ",
        "valid_syntax_label": "صحة بناء SQL",
        "performance_over_time": "الأداء مع مرور الوقت",
        "query_trend": "اتجاه نجاح الاستعلامات",
        "confidence_trend": "اتجاه الثقة في النموذج",
        "no_history_data": "لا توجد بيانات أداء للنموذج بعد.",
        "erd_diagram": "مخطط العلاقات بين الجداول",
        "chatbot_title": "المساعد الذكي",
        "chatbot_subtitle": "اسأل مساعد SQLWhisper أي شيء — من استفسارات SQL إلى إرشادات النظام.",
        "chatbot_greeting": "مرحباً! أنا مساعد SQLWhisper 🤖",
        "chatbot_schema_question": "هل ترغب في تحميل هيكل قاعدة بياناتك أو المتابعة بقاعدة البيانات التجريبية؟",
        "upload_schema_btn": "تحميل قاعدة البيانات",
        "use_default_btn": "استخدام التجريبية",
        "upload_prompt": "قم بتحميل ملف SQLite أو DB أو CSV",
        "uploaded_success": "تم التحميل بنجاح!",
        "chatbot_ready_after_upload": "رائع! تم تجهيز بياناتك، يمكنك الآن طرح أسئلة SQL.",
        "chatbot_default_reply": "خيار رائع! سيتم استخدام قاعدة البيانات التجريبية، ابدأ بطرح سؤالك الأول.",
        "chat_placeholder": "اكتب سؤالك هنا...",
        "chat_generating": "جارٍ توليد الرد...",
        "chat_error_no_reply": "لم يتم استلام رد من النموذج.",
        "chat_error_server": "حدث خطأ من الخادم.",
        "chat_error_connection": "تعذّر الاتصال بالخادم.",
        "chat_connect_instruction": "اضغط أدناه للاتصال بمساعد SQLWhisper قبل بدء الدردشة.",
        "connect_backend": "الاتصال بالخادم",
        "checking_connection": "جارٍ التحقق من الاتصال...",
        "backend_connected_ok": "تم الاتصال بالخادم بنجاح.",



        # Tabs
        "query_tab": "الاستعلام",
        "history_tab": "السجل",
        "feedback_tab": "مراجعة الملاحظات",
        "dashboard_tab": "لوحة التحكم",
        "about_tab": "حول",

        # Sidebar / system
        "database_info": "معلومات قاعدة البيانات",
        "load_schema": "تحميل هيكل قاعدة البيانات",
        "loading_schema": "جارِ تحميل هيكل قاعدة البيانات...",
        "db_connected": "تم الاتصال بقاعدة البيانات",
        "db_failed": "فشل تحميل معلومات قاعدة البيانات",

        # Headers / sections
        "ask_question": "اسأل سؤالاً",
        "quick_queries": "استعلامات سريعة",
        "your_question": "سؤالك",
        "placeholder": "صف ما تريد معرفته عن بياناتك...",
        "generated_sql": "الاستعلام المُولد",
        "rate_sql": "قيّم هذا الاستعلام",
        "test_corrected": "جرّب الاستعلام المصحّح",
        "corrected_results": "نتائج الاستعلام المصحّح",
        "query_results": "نتائج الاستعلام",
        "raw_model_output": "عرض مخرجات النموذج الخام",
        "user_feedback_review": "مراجعة ملاحظات المستخدمين",
        "system_db_dashboard": "لوحة النظام وقاعدة البيانات",
        "database_overview": " نظرة عامة على قاعدة البيانات",
        "schema_details": " تفاصيل المخطط",
        "query_model_insights": "رؤى الاستعلام والنموذج",
        "about_sqlwhisper": "حول SQLWhisper",
        "system_status": "حالة النظام",

        # Buttons
        "generate_sql": " توليد استعلام SQL",
        "clear_results": "مسح النتائج",
        "looks_good": " جيد",
        "needs_improvement": "يحتاج تحسين",
        "execute_corrected": "تنفيذ الاستعلام المصحّح",
        "download_corrected": "تنزيل نتائج الاستعلام المصحّح",
        "download_results_csv": "تنزيل النتائج كملف CSV",
        "download_history": "تنزيل سجل الاستعلامات",
        "download_feedback": "تنزيل ملاحظات المستخدمين",

        # Inputs / feedback
        "what_was_wrong": "ما الخطأ؟",
        "corrected_sql_optional": "استعلامك المصحّح (اختياري):",

        # Messages / statuses
        "backend_not_running": "خادم FastAPI غير قيد التشغيل! يرجى تشغيله أولاً.",
        "start_server_cmd": "python app.py",
        "enter_question_first": "يرجى إدخال سؤال أولاً.",
        "generating_sql": "جارِ توليد الاستعلام...",
        "sql_generated_ok": "تم توليد الاستعلام بنجاح!",
        "api_error": "خطأ في واجهة البرمجة",
        "request_failed": "فشل الطلب",
        "only_select_allowed": "يُسمح فقط باستعلامات SELECT حفاظاً على الأمان.",
        "enter_sql_before_exec": "يرجى إدخال استعلام SQL قبل التنفيذ.",
        "sql_exec_error": " خطأ في تنفيذ SQL",
        "query_exec_success": " تم تنفيذ الاستعلام بنجاح — عرض {n_rows} صفاً.",
        "thanks_feedback": "شكراً على ملاحظاتك! ",
        "failed_save_feedback": "فشل حفظ الملاحظات",
        "feedback_saved_down": "تم حفظ الملاحظة مع التصحيح ",
        "sql_syntax": "بناء الجملة SQL",
        "valid": "صحيح",
        "invalid": "غير صحيح",
        "execution": "التنفيذ",
        "success": "ناجح",
        "failed": "فشل",
        "results": "النتائج",
        "rows": "صفوف",
        "no_data": "لا توجد بيانات",
        "exec_error": "خطأ بالتنفيذ",
        "no_raw_output": "لا توجد مخرجات خام",
        "no_history_yet": "لا يوجد سجل بعد. سيتم إنشاؤه عند أول استعلام.",
        "no_query_history": "لا يوجد سجل للاستعلامات بعد. ابدأ بطرح سؤال في تبويب الاستعلام!",
        "error_loading_history": "خطأ في تحميل السجل",
        "total_queries": "إجمالي الاستعلامات",
        "successful": "ناجحة",
        "valid_sql": "SQL صحيح",
        "success_rate": "معدل النجاح",
        "feedback_total": "إجمالي الملاحظات",
        "filter_by_verdict": "تصفية حسب التقييم:",
        "all": "الكل",
        "up": "up",
        "down": "down",
        "no_feedback": "لا توجد ملاحظات بعد.",
        "error_loading_feedback": "خطأ في تحميل الملاحظات",
        "total_tables": "إجمالي الجداول",
        "total_rows": "إجمالي الصفوف",
        "query_success_trend": "اتجاه نجاح الاستعلامات",
        "model_conf_trend": "اتجاه ثقة النموذج",
        "no_query_yet_run": "لا يوجد سجل للاستعلامات بعد. قم بتشغيل بعض الاستعلامات أولاً.",
        "error_loading_dashboard": "خطأ في تحميل لوحة التحكم",
        "backend_status": "حالة الخادم",
        "operational": "يعمل",
        "not_available": "غير متاح",
        "database": "قاعدة البيانات",
        "connected_tables": "متصل ({n_tables} جدولاً)",
        "not_loaded": "غير محمّلة",
        "confidence_unavailable": "درجة الثقة غير متاحة من النموذج.",
        "confidence_label": "الثقة: {conf}% ({label})",
        
        "history_columns": {
        "timestamp": "الوقت",
        "question": "السؤال",
        "sql_query": "الاستعلام",
        "success": "النجاح",
        "valid_sql": "صحة SQL",
        "rows_returned": "عدد الصفوف",
        "error_message": "الخطأ",
        "confidence": "الثقة",
        "confidence_label": "مستوى الثقة"
    },
   "feedback_columns": {
    "question": "السؤال",
    "generated_sql": "الاستعلام المُولّد",
    "user_correction": "التصحيح من المستخدم",
    "verdict": "التقييم",
    "reason": "السبب",
    "comment": "الملاحظات",
    "created_at": "تاريخ الإضافة"
    },

    "verdict_labels": {
        "up": "جيد",
        "down": "يحتاج تحسين"
    },
    "success_labels": {
        True: "ناجح",
        False: "فشل"
    },
    "valid_sql_labels": {
        True: "صحيح",
        False: "غير صحيح"
    },
    "confidence_labels": {
        "High": "عالية",
        "Medium": "متوسطة",
        "Low": "منخفضة"
    },
    "generate_summary": "إنشاء الملخص",
    "summary_box_title": "أهم النتائج",
    "summary_failed": "فشل إنشاء الملخص",
    "summary_warning": "تعذر إنشاء الملخص",

        # About text (Arabic)
        "about_rich_html": """
        <div style='background: linear-gradient(135deg, #f5f0ff, #e6e6ff); padding: 2rem; border-radius: 1rem; border-left: 6px solid #8a2be2;'>
        <h3 style='color: #6a0dad; margin-top: 0;'>توليد استعلامات SQL مدعوم بالذكاء الاصطناعي</h3>
        يحوّل SQLWhisper أسئلتك باللغة الطبيعية إلى استعلامات SQL دقيقة، 
        ليجعل التفاعل مع قواعد البيانات بديهياً ومتاحاً للجميع.
        <h4 style='color: #6a0dad;'>الميزات الرئيسية:</h4>
        <ul>
        <li><strong>معالجة اللغة الطبيعية</strong> — اطرح أسئلة باللغة العادية</li>
        <li><strong>اكتشاف المخطط الذكي</strong> — يفهم بنية قاعدة بياناتك تلقائياً</li>
        <li><strong>التحقق من صحة SQL</strong> — ضمان صحة بناء الاستعلامات</li>
        <li><strong>تنفيذ فوري</strong> — نفّذ الاستعلامات وشاهد النتائج مباشرةً</li>
        <li><strong>نتائج تفاعلية</strong> — فرز وتصنيف واستكشاف بياناتك بسهولة</li>
        </ul>
        <h4 style='color: #6a0dad;'>تميّز تقني:</h4>
        <ul>
        <li>خلفية قوية باستخدام FastAPI</li>
        <li>نماذج لغوية مفتوحة المصدر متقدمة</li>
        <li>تحقّق لحظي من صياغة SQL</li>
        <li>تحليلات وسجل استعلامات شامل</li>
        </ul>
        </div>
        """,
      


    }
    
} 
def t(key: str, lang: str = "en") -> str:
    """Return translation for a given key and language."""
    return text_labels.get(lang, text_labels["en"]).get(key, key)