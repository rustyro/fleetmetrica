from cli.service import CLI, parser


parsed_args = parser.parse_args()


cli = CLI(parsed_args)
try:
    cli.run()
except:
    pass
cli.flush_logs_to_db()

